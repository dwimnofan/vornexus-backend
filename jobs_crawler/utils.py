import re

# Define common job categories and their keywords
JOB_CATEGORIES = {
    'IT': [
        'software', 'developer', 'engineer', 'programming', 'code', 'python', 'java', 'javascript',
        'web', 'frontend', 'backend', 'fullstack', 'devops', 'cloud', 'aws', 'azure', 'data scientist',
        'machine learning', 'ai', 'artificial intelligence', 'database', 'sql', 'nosql', 'it', 
        'information technology', 'computer', 'tech', 'technology', 'system administrator', 'network',
        'security', 'cybersecurity', 'qa', 'quality assurance', 'testing', 'mobile', 'android', 'ios',
        'react', 'angular', 'vue', 'node', 'django', 'flask', 'spring', 'dotnet', '.net'
    ],
    'Marketing': [
        'marketing', 'digital marketing', 'seo', 'sem', 'social media', 'content', 'brand', 'branding',
        'advertising', 'market research', 'pr', 'public relations', 'communications', 'growth hacker',
        'growth marketing', 'campaign', 'email marketing', 'copywriter', 'copywriting', 'content writer',
        'content marketing', 'marketing manager', 'marketing director', 'cmo', 'chief marketing officer'
    ],
    'Sales': [
        'sales', 'account executive', 'account manager', 'business development', 'sales representative',
        'sales manager', 'sales director', 'customer success', 'client', 'customer', 'cro', 
        'chief revenue officer', 'vp of sales', 'inside sales', 'outside sales', 'sales associate'
    ],
    'Finance': [
        'finance', 'accounting', 'accountant', 'financial', 'analyst', 'investment', 'banking',
        'bookkeeper', 'bookkeeping', 'cfo', 'chief financial officer', 'controller', 'treasurer',
        'auditor', 'audit', 'tax', 'payroll', 'budget', 'financial planning', 'fp&a'
    ],
    'HR': [
        'hr', 'human resources', 'recruiter', 'recruiting', 'talent acquisition', 'people operations',
        'people manager', 'hiring', 'onboarding', 'benefits', 'compensation', 'chro', 
        'chief human resources officer', 'hr manager', 'hr director', 'hr business partner', 'hrbp'
    ],
    'Customer Service': [
        'customer service', 'customer support', 'help desk', 'call center', 'support specialist',
        'customer success', 'customer experience', 'cx', 'service representative'
    ],
    'Administrative': [
        'administrative', 'admin', 'office manager', 'receptionist', 'secretary', 'executive assistant',
        'personal assistant', 'office coordinator', 'clerical', 'data entry'
    ],
    'Healthcare': [
        'healthcare', 'health', 'medical', 'nurse', 'doctor', 'physician', 'dentist', 'dental',
        'pharmacist', 'pharmacy', 'clinical', 'therapist', 'therapy', 'caregiver', 'care', 'patient'
    ],
    'Education': [
        'education', 'teacher', 'professor', 'instructor', 'tutor', 'teaching', 'school', 'university',
        'college', 'academic', 'principal', 'dean', 'faculty', 'curriculum', 'educational'
    ],
    'Engineering': [
        'engineering', 'mechanical engineer', 'electrical engineer', 'civil engineer', 'structural engineer',
        'chemical engineer', 'biomedical engineer', 'aerospace engineer', 'industrial engineer',
        'environmental engineer', 'petroleum engineer', 'architectural engineer', 'engineer'
    ],
    'Design': [
        'design', 'designer', 'graphic design', 'ui', 'ux', 'user interface', 'user experience',
        'product design', 'web design', 'creative', 'art director', 'artist', 'illustrator'
    ],
    'Legal': [
        'legal', 'lawyer', 'attorney', 'paralegal', 'law', 'counsel', 'compliance', 'contract',
        'litigation', 'regulatory', 'general counsel', 'legal assistant'
    ],
    'Operations': [
        'operations', 'operation', 'logistics', 'supply chain', 'procurement', 'purchasing',
        'inventory', 'warehouse', 'production', 'manufacturing', 'quality control', 'process improvement',
        'operational', 'coo', 'chief operations officer', 'operations manager'
    ]
}

def categorize_job(title, description):
    """
    Categorize a job based on its title and description
    Returns the most likely category
    """
    title = title.lower()
    description = description.lower()
    
    # Combine title and description, giving more weight to the title
    text = title + " " + title + " " + description
    
    # Count matches for each category
    category_scores = {}
    
    for category, keywords in JOB_CATEGORIES.items():
        score = 0
        for keyword in keywords:
            # Use word boundaries to match whole words
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            matches = re.findall(pattern, text)
            score += len(matches)
        
        category_scores[category] = score
    
    # Find the category with the highest score
    if category_scores:
        max_category = max(category_scores.items(), key=lambda x: x[1])
        
        # If we have a match with a score > 0, return that category
        if max_category[1] > 0:
            return max_category[0]
    
    # Default category if no matches found
    return "Other"
