import os
from huey.contrib.djhuey import task
from dotenv import load_dotenv
from cv.models import CV
from core.ai.pm import PromptManager
from matching.models import JobRecommendation 
from jobs.models import Job  # import model Job
from jobs.utils import get_collection_by_category

from pydantic import BaseModel, Field
from typing import List, Literal
from django.utils import timezone
from datetime import date
from notifications.methods import send_notification


load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class MatchedJob(BaseModel):
    job_id : str = Field(..., description="Unique identifier for the job")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    match_score: float = Field(..., description="Total requirements that match this job on a scale of 0-100%")
    matched_skills: List[str] = Field(..., description="List of matched skills between CV and job") 
    required_skills: List[str] = Field(..., description="List of required skills")
    job_description: str = Field(..., description="Job description")
    apply_link: str = Field(..., description="Link to apply for the job")
    reason: str = Field(..., description="Reason for the match score and job match")
    url: str = Field(..., description="Unique job URL")
    job_type: str = Field(..., description="Type of job, e.g. full-time, part-time")
    industry: str = Field(..., description="Industry the job belongs to")
    experience_level: str = Field(..., description="Experience level required for the job")
    education_level: str = Field(..., description="Education level required for the job")
    skills_required: str = Field(..., description="All required skills in string format")
    date_posted: date = Field(..., description="Date the job was posted")

class MatchingJob(BaseModel):
    jobs: List[MatchedJob] = Field(description="List of matched jobs")


CATEGORY_KEYWORDS = {
    "Teknologi": [
        "software engineer", "devops engineer", "data scientist",
        "cybersecurity analyst", "qa engineer", "ui/ux designer", "cloud engineer",
        "backend", "frontend", "full stack", "mobile developer", "machine learning", "data analyst", "qa tester"
    ],
    "Bisnis dan Manajemen": [
        "business analyst", "project manager", "product manager",
        "hr specialist", "recruiter", "marketing specialist", "digital marketing",
        "finance analyst", "accountant"
    ],
    "Kreatif": [
        "graphic designer", "ui designer", "content writer", "copywriter",
        "video editor", "social media specialist", "brand strategist"
    ],
    "Industri dan Manufaktur": [
        "mechanical engineer", "industrial engineer", "supply chain analyst",
        "procurement specialist", "quality assurance engineer", "qa manufaktur", "qa logistik"
    ]
}

CategoryLiteral = Literal["Teknologi", "Bisnis dan Manajemen", "Kreatif", "Industri dan Manufaktur"]

class AnalyzeCVCategory(BaseModel):
    category: CategoryLiteral = Field(
        ..., 
        description="Category of the job, must be one of: Teknologi, Bisnis dan Manajemen, Kreatif, Industri dan Manufaktur"
    )

def analyze_cv_category(cv_text: str) -> AnalyzeCVCategory:
    pm = PromptManager()
    pm.add_message("system", f"""

    Kamu adalah asisten yang bertugas menganalisis isi CV dan menentukan kategori pekerjaan yang paling sesuai.

    Kategori yang tersedia:
    1. Teknologi
    2. Bisnis dan Manajemen
    3. Kreatif
    4. Industri dan Manufaktur

    Berikan hasil dalam format JSON hanya dengan field `category`.

    CV:
    {cv_text}
    """)
    pm.add_message("user", "Tentukan kategori pekerjaan yang paling sesuai dengan CV di atas.")
    result = pm.generate_structure(AnalyzeCVCategory)
    return result
    
@task()
def job_matching(user, cv_id):
    pm = PromptManager()
    cv = CV.objects.filter(id=cv_id).first()
    if not cv:
        print(f"CV dengan id {cv_id} tidak ditemukan.")
        return

    parsed_cv = cv.parsed_text
    category = analyze_cv_category(parsed_cv)
    print(f"Kategori pekerjaan yang dianalisis: {category['category']}")
    collection = get_collection_by_category(category["category"])
    print("Total jobs in collection:", collection.count())

    result = collection.query(
        query_texts=[parsed_cv],
        n_results=30,
        include=["documents", "distances", "metadatas"],
    )


    documents = result.get("documents", [[]])[0]
    print("Result:", result)
    formatted_jobs = ""
    for i, doc in enumerate(documents, 1):
        formatted_jobs += f"Lowongan {i}:\n{doc.strip()}\n\n"

    pm.add_message("system", f"""
            You are an advanced AI-powered career consultant and job-matching specialist with deep expertise in talent acquisition, career development, and industry trends. Your mission is to provide highly accurate, personalized job recommendations using sophisticated analysis techniques that prioritize job freshness and market timing.

            ## ANALYSIS FRAMEWORK

            ### 1. MULTI-DIMENSIONAL SCORING SYSTEM (Enhanced Weights with Time Factor)

            **Job Freshness & Market Timing (20%)**
            - Job posting recency and urgency indicators
            - Application deadline proximity and hiring timeline
            - Market demand trends and seasonal hiring patterns
            - Competition level assessment based on posting age
            - Hiring velocity and company recruitment momentum

            **Technical Skills Alignment (25%)**
            - Hard skills match: Programming languages, frameworks, tools, technologies
            - Soft skills alignment: Communication, leadership, problem-solving
            - Skill depth assessment: Beginner/Intermediate/Advanced/Expert levels
            - Technology stack compatibility and modernness
            - Domain-specific expertise (AI/ML, DevOps, Frontend, Backend, etc.)

            **Professional Experience Relevance (30%)**
            - Role responsibility alignment with job duties
            - Industry experience and sector knowledge
            - Project complexity and scale similarity
            - Achievement quantification and impact measurement
            - Career trajectory and growth pattern analysis
            - Cross-functional experience value

            **Educational & Certification Match (8%)**
            - Degree relevance and prestige
            - Professional certifications and their currency
            - Continuous learning indicators
            - Specialized training and bootcamps
            - Academic achievements and research experience

            **Seniority & Career Level Fit (12%)**
            - Years of experience appropriateness
            - Leadership and management experience alignment
            - Team size and budget responsibility match
            - Decision-making authority level compatibility
            - Mentoring and training experience

            **Company & Role Compatibility (5%)**
            - Company size preference (startup/scale-up/enterprise)
            - Work environment fit (remote/hybrid/on-site)
            - Industry sector alignment and interest
            - Company culture and values match
            - Growth opportunity alignment
            - Compensation expectation compatibility

            ### 2. TIME-BASED PRIORITIZATION MATRIX

            **🔥 URGENT (Posted within 0-3 days)**
            - **Priority Score Multiplier: 1.5x**
            - Immediate action required
            - High application success probability
            - Limited competition window
            - Fast-track interview process likely

            **⚡ HIGH PRIORITY (Posted within 4-7 days)**
            - **Priority Score Multiplier: 1.3x**
            - Strong application timing
            - Moderate competition level
            - Good visibility with recruiters
            - Standard interview timeline

            **📈 GOOD TIMING (Posted within 8-14 days)**
            - **Priority Score Multiplier: 1.1x**
            - Reasonable application window
            - Building competition
            - Still within optimal range
            - Normal hiring process

            **⏰ TIME-SENSITIVE (Posted within 15-21 days)**
            - **Priority Score Multiplier: 1.0x**
            - Standard application timing
            - Increased competition likely
            - May need compelling application
            - Longer hiring process possible

            **⚠️ AGING (Posted within 22-30 days)**
            - **Priority Score Multiplier: 0.9x**
            - High competition probability
            - May indicate difficult requirements
            - Requires exceptional application
            - Potential for multiple interview rounds

            **❌ STALE (Posted 30+ days ago)**
            - **Priority Score Multiplier: 0.7x**
            - Very high competition
            - Possible role difficulty or unrealistic requirements
            - May have internal candidates
            - Consider only if exceptional match (90%+)

            ### 3. ADVANCED MATCHING ALGORITHMS (Time-Enhanced)

            **Temporal Semantic Analysis**: Prioritize recent skills and technologies mentioned in fresh job postings

            **Competition-Adjusted Gap Analysis**: Weight skill gaps based on posting age and expected competition level

            **Hiring Momentum Assessment**: Evaluate company's recent hiring patterns and growth trajectory

            **Market Timing Optimization**: Consider seasonal hiring trends and industry-specific recruitment cycles

            **Application Strategy Timing**: Factor in optimal application timing based on posting freshness

            ### 4. ENHANCED SCORING RUBRIC (Time-Weighted)

            **95-100: Perfect Match** 🎯
            - 95%+ requirement alignment
            - Posted within 7 days (Urgent/High Priority)
            - Ideal experience level and trajectory
            - Strong cultural and technical fit
            - Immediate productivity potential

            **85-94: Exceptional Match** ⭐
            - 85-94% requirement alignment  
            - Posted within 14 days (Good timing or better)
            - Minor, easily bridgeable gaps
            - Strong growth potential in role
            - High interview success probability

            **75-84: Strong Match** 💪
            - 75-84% requirement alignment
            - Posted within 21 days (Time-sensitive or better)
            - Good foundation with some skill gaps
            - Clear development path available
            - Solid long-term potential

            **65-74: Good Match** ✅
            - 65-74% requirement alignment
            - Any posting age acceptable with strong fundamentals
            - Moderate development needed
            - Transferable skills present
            - Worth pursuing with preparation

            **55-64: Fair Match** ⚠️
            - 55-64% requirement alignment
            - Only consider if posted within 14 days
            - Significant but addressable gaps
            - Requires substantial upskilling
            - Consider for growth-oriented roles

            **45-54: Weak Match** ❌
            - 45-54% requirement alignment
            - Only consider if posted within 7 days and urgent hiring need
            - Major gaps in critical areas
            - High development investment needed
            - Low success probability

            **Below 45: Poor Match** 🚫
            - Fundamental misalignment
            - Not recommended regardless of posting time
            - Core requirements not met

            ### 5. TIME-AWARE OUTPUT REQUIREMENTS

            For each recommended job, provide:

            1. **Match Score & Time-Adjusted Rating**: Base score + time multiplier = final priority score
            2. **Posting Freshness Alert**: Days since posting with urgency indicator
            3. **Application Timing Strategy**: Optimal application timing and deadline awareness
            4. **Competition Level Assessment**: Expected number of applicants based on posting age
            5. **Strengths Analysis**: Top 3-5 alignment strengths
            6. **Gap Analysis**: Key missing requirements and their criticality
            7. **Recommendation Rationale**: Why this job fits considering timing factors
            8. **Action Items**: Time-specific steps to strengthen candidacy
            9. **Application Urgency**: Immediate/This week/Within 2 weeks/Consider carefully
            10. **Timeline Assessment**: Ready now / 3-6 months / 6+ months preparation needed
            11. **Interview Preparation Tips**: Role-specific advice with timing considerations
            12. **Salary Expectation Alignment**: Market rate vs posting age correlation

            ### 6. CONTEXTUAL CONSIDERATIONS (Time-Enhanced)

            - **Posting Recency Priority**: Fresh postings (0-7 days) receive significant preference
            - **Seasonal Hiring Patterns**: Consider Q1 hiring surge, summer slowdown, Q4 budget cycles
            - **Industry-Specific Timing**: Tech hiring peaks, finance bonus cycles, startup funding rounds
            - **Economic Climate Awareness**: Current market conditions affecting hiring velocity
            - **Company Hiring Momentum**: Recent job posting frequency indicating growth vs downsizing
            - **Application Deadline Proximity**: Factor in stated deadlines or inferred urgency
            - **Weekend/Holiday Posting Strategy**: Consider posting timing for application strategy

            ### 7. POSTING TIME ANALYSIS REQUIREMENTS

            For each job recommendation, analyze and report:

            **📅 Posting Timeline Analysis:**
            - Exact posting date and age in days
            - Day of week posted (strategy implications)
            - Posting pattern analysis (batch posting vs individual)
            - Update/refresh history if available

            **⚡ Urgency Indicators:**
            - Explicit deadlines mentioned
            - "Immediate start" or "ASAP" language
            - Multiple similar roles posted simultaneously
            - Hiring manager contact provided
            - Expedited interview process mentioned

            **📊 Competition Assessment:**
            - Estimated applications based on posting age
            - View count or engagement metrics if available
            - Similar role availability in market
            - Company size vs role visibility ratio

            ## JOB CONTEXT DATA
            {formatted_jobs}

            ## CRITICAL INSTRUCTIONS

            1. **TIME-FIRST PRIORITIZATION**: Always lead with posting recency in ranking decisions
            2. **STRICT ADHERENCE**: Use ONLY the provided job postings with their exact posting dates
            3. **QUANTITATIVE ANALYSIS**: Provide specific percentages, days since posting, and time multipliers
            4. **ACTIONABLE TIMING**: Include concrete next steps with time-sensitive recommendations
            5. **HONEST TEMPORAL ASSESSMENT**: Highlight both opportunities and time-based challenges
            6. **STRATEGIC PRIORITIZATION**: Rank by combined match quality and time advantage
            7. **INDUSTRY TIMING INSIGHTS**: Provide context about hiring cycles and market timing
            8. **APPLICATION DEADLINE AWARENESS**: Flag approaching deadlines or optimal application windows

            ## EXPECTED OUTPUT FORMAT

            ### Job Recommendation Structure:
            ```
            ### Rank #X: [Job Title] at [Company]
            **Time-Adjusted Match Score: XX/100** [Rating Badge] 
            **Base Match: XX/100 | Time Multiplier: X.Xx | Final Priority: XX/100**
            **Posted: X days ago** [Urgency Badge: 🔥/⚡/📈/⏰/⚠️/❌]

            **⏰ TIMING ANALYSIS:**
            - Application Window: [Immediate/This Week/Within 2 weeks/Consider Carefully]
            - Competition Level: [Low/Moderate/High/Very High]
            - Hiring Urgency: [Critical/High/Normal/Relaxed]

            [Continue with standard match analysis...]
            ```

            This time-aware system ensures candidates apply to the freshest opportunities with the highest success probability while maintaining quality matching standards.
            """)

    pm.add_message("user",f"""
        **CANDIDATE PROFILE TO ANALYZE:**
        {parsed_cv}

        **ANALYSIS REQUEST:**
        Please provide the TOP 10 most strategically valuable job recommendations using your advanced matching framework.

        **REQUIRED OUTPUT FORMAT:**

        # 🎯 ADVANCED JOB RECOMMENDATIONS REPORT

        ## Executive Summary
        [Brief overview of candidate's profile and market positioning]

        ## Top 10 Strategic Job Matches

        ### Rank #1: [Job Title] at [Company]
        **Match Score: XX/100** [Rating Badge]
        **Strategic Value: ⭐⭐⭐⭐⭐**

        **🔍 Match Analysis:**
        - Technical Alignment: XX%
        - Experience Relevance: XX%  
        - Growth Potential: XX%
        - Market Value: XX%

        **💪 Key Strengths:**
        - [Specific alignment point 1]
        - [Specific alignment point 2]
        - [Specific alignment point 3]

        **⚠️ Development Areas:**
        - [Gap 1] - [Criticality: High/Medium/Low]
        - [Gap 2] - [Criticality: High/Medium/Low]

        **🎯 Why This Role:**
        [Strategic rationale for recommendation]

        **📈 Action Plan:**
        1. [Immediate action]
        2. [Short-term preparation]
        3. [Skill development priority]

        **⏰ Timeline:** [Ready Now/3-6 months/6+ months]

        ---

        [Repeat format for ranks #2-10]

        ## 📊 SUMMARY INSIGHTS

        **Strongest Career Paths:**
        - [Path 1]: [Rationale]
        - [Path 2]: [Rationale]

        **Market Positioning:**
        [Overall assessment of candidate's competitiveness]

        **Priority Development Areas:**
        1. [Skill/area 1]
        2. [Skill/area 2]
        3. [Skill/area 3]

        **Salary Range Expectations:**
        [Based on matched roles and experience level]
        """)
    result = pm.generate_structure(MatchingJob)
    matched_jobs = result.get('jobs')
    print("Matched Jobs:", matched_jobs)

    for idx, job in enumerate(matched_jobs, 1):
        job_instance = Job.objects.filter(job_hash=job['job_id']).first()
        if job_instance:
            # Buat JobRecommendation, jika sudah ada, skip
            JobRecommendation.objects.filter(user=user, job=job_instance).delete()
            recommendation, created_rec = JobRecommendation.objects.update_or_create(
                user=user,
                job=job_instance,
                defaults={
                    "score": job["match_score"],
                    "recommended_at": timezone.now()
                },
                matched_skills=job["matched_skills"],
                reason=job["reason"]
            )

            if created_rec:
                print(f"✅ JobRecommendation #{idx} berhasil disimpan untuk user {user.username}.")
            else:
                print(f"⚠️ JobRecommendation #{idx} sudah ada untuk user {user.username}, dilewati.")
        else:
            print(f"❌ Job {job['title']} di {job['company']} tidak ditemukan di database.")

    send_notification("Mathcing jobs completed")