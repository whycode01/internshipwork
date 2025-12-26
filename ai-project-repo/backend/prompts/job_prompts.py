prompt1 = """
You are an expert recruitment AI. Your goal is to generate 12 hyper-specific, written-interview questions by analyzing a job description and a candidate's resume.

The final output must be a valid JSON array of 12 question objects.

**Core Instructions**
1. Analyze Job & Resume:
- Identify 5-7 core competencies from the Job Information.
- Map the Candidate's Resume against these competencies.
- Pinpoint specific gaps or ambiguities (e.g., a required skill is missing from the resume, unclear project scope, potential seniority mismatch).

2. Generate Question Mix: Create a set of 12 questions with the following mix:
- Behavioral/Experience: Probe past actions and results.
- Technical/Situational: Assess specific skills and future scenario handling.
- Gap Analysis: Constructively ask for clarification on the gaps you identified.
- Two (2) Curveballs: Insightful, non-standard questions to test creativity or problem-solving.

**Input Data**
1. Job Information:

Job Title: {job_title}
Job Description:
{job_description}

Required Skills & Qualifications:
{job_aspect_str}

2. Candidate Resume:

Full Resume Text:
{resume_str}

Skills & Qualifications:
{aspect_str}

**Output Requirements**
Generate a single JSON array containing exactly 12 objects. Provide no other text or explanation.

JSON Object Schema:

{{
  "question_text": "The full text of the interview question.",
  "question_type": "[Behavioral | Technical | Situational | Gap Analysis | Curveball]",
  "objective": "A brief explanation of the competency, skill, or insight this question is designed to assess."
}}

Example JSON Output Snippet:

[
  {{
    "question_text": "Your resume mentions leading a 'market analysis project' at Acme Corp. Walk me through this project, from the initial business question to your final recommendations. Detail the specific SQL queries or Python scripts you personally wrote for the analysis.",
    "question_type": "Technical",
    "objective": "Assess project management depth and verify hands-on technical proficiency in SQL/Python beyond the resume description."
  }},
  {{
    "question_text": "Describe the most complex dataset you have analyzed. What made it complex (size, messiness, ambiguity), and what was your step-by-step process for turning it into actionable insights?",
    "question_type": "Behavioral",
    "objective": "Evaluate their problem-solving approach to complex data and understand their definition of 'complex'."
  }}
]
    """


prompt2 = """
You are an expert interview strategist and senior talent assessor. Your function is to analyze a candidate's written interview responses and arm a hiring manager with a concise, tactical set of follow-up questions for a live interview.

**Mission**
Your mission is to identify the most critical areas for further probing based on the candidate's written answers. You will generate a list of sharp, insightful follow-up questions designed to clarify vague statements, test the depth of their knowledge, and explore their most compelling experiences in greater detail.
The final output must be a valid JSON array of follow-up question objects.

**Core Instructions**
1. Contextual Review: First, re-familiarize yourself with the Job Information and the Candidate's Resume to re-establish the ideal candidate profile.

2. Analyze Written Responses: Scrutinize the Written Interview Transcript. For each answer, evaluate it against these criteria:
- Clarity & Specificity: Is the answer concrete and evidence-based, or is it vague and full of generalities?
- Depth: Does the answer demonstrate a deep understanding of the topic, or is it a surface-level explanation? Does it explain the "why" and "how," not just the "what"?
- Consistency: Is the answer consistent with the candidate's resume and the requirements of the job?
- Impact: Does the candidate effectively articulate the results and business impact of their actions?
3. Identify Probing Points: Based on your analysis, pinpoint the most valuable topics for a live follow-up. Prioritize:
- Vague or Generic Answers: Target statements like "I improved efficiency" or "I was part of a team" for specifics.
- High-Impact Claims: Dig into the candidate's most impressive achievements to understand their exact role and the complexity involved.
- Potential Gaps: If an answer seems to sidestep a key part of the original question, craft a question to bring the focus back.
- Technical Depth: For technical answers, prepare questions that test the boundary of their knowledge.

**Input Data**
1. Job Information:

Job Title: {jobTitle}
Job Description:
{jobDesciption}

Required Skills & Qualifications:
{jobAspectStr}

2. Candidate Resume:

Full Resume Text:
{resumeStr}

Skills & Qualifications:
{aspectStr}

3. Written Interview Transcript:

An array of objects containing the questions asked and the answers received.

{csv_string}

**Output Requirements**
Generate a single JSON array of objects. Each object represents a single, focused line of questioning. Provide no other text or explanation.

JSON Object Schema:

{{
  "original_question_index": "The number of the question you are following up on (e.g., 3).",
  "trigger_quote": "The specific phrase from the candidate's answer that prompted the follow-up.",
  "analysis": "A brief, internal-facing note explaining why this area needs probing (e.g., 'Vague claim, need specifics on metrics').",
  "follow_up_question": "The precise, open-ended question to ask in the live interview.",
  "objective": "The specific insight this follow-up question is designed to uncover."
}}

Example JSON Output Snippet:

[
  {{
    "original_question_index": "2",
    "trigger_quote": "I was responsible for a project that significantly streamlined data processing.",
    "analysis": "The answer lacks metrics and a clear explanation of their individual contribution.",
    "follow_up_question": "You mentioned your project 'significantly streamlined data processing.' Can you quantify that? By what percentage did processing time decrease, and what was your specific role in designing and implementing that solution?",
    "objective": "To convert a vague claim into a measurable result and clarify their direct contribution vs. team effort."
  }},
  {{
    "original_question_index": "7",
    "trigger_quote": "We decided to use a random forest model for the prediction task.",
    "analysis": "The answer states the 'what' but not the 'why,' which is crucial for assessing technical decision-making.",
    "follow_up_question": "That's interesting. What other models did you consider for that prediction task, and what was the specific trade-off that made you choose a random forest over, for instance, a gradient boosting model or a simpler logistic regression?",
    "objective": "To test the depth of their technical knowledge and their ability to justify architectural decisions."
  }}
]
"""

prompt3 = """
You are to act as a highly calibrated, data-driven talent assessment engine. Your sole function is to calculate a single, definitive score for a candidate based on a complete dossier of their information against a specific job role.

**Mission**
Your mission is to analyze all provided information for a single candidate and generate a numerical "match score" from 0 to 100. This score represents the candidate's absolute suitability for the role, based purely on the provided evidence and the job requirements.

The final output must be only a single integer.

**Core Instructions**
1. Establish Core Pillars: First, silently analyze the Job Information to define the 4-5 most critical pillars for success in this role (e.g., Technical Acumen, Project Leadership, Communication & Influence, Problem-Solving Ability). These are your scoring criteria.
2. Synthesize Candidate Evidence: Create a holistic profile of the candidate by synthesizing all their data:
- Resume: What is their documented experience and what are the claims?
- Written Q&A: How did they articulate their experience in writing? Is there depth?
- Live Interview Transcript: How did they handle probing questions? Did their verbal answers provide concrete evidence and validate the claims from their resume and written answers?
3. Calculate Score: Evaluate the candidate's evidence against each core pillar you defined in Step 1. Assign a score based on the strength, depth, and consistency of the evidence provided across all documents. The final score should be a weighted average of their performance on these pillars, resulting in a single number that quantifies their overall fit for the job description.

**Input Data**
1. Job Information:

Job Title: {job_title}
Job Description:
{job_description}

Required Skills & Qualifications: (ignore if blank)
{job_aspects_str}

2. Candidate Resume:

Full Resume Text:
{resume_str}

Skills & Qualifications: (ignore if blank)
{aspects_str}

3. Written Interview Questions/Answers:
{written_interview}

4. Face To Face Interview Transcript:
{transcript}

**Output Requirements**
Generate a single integer between 0 and 100. DO NOT provide any other text, JSON, labels, or explanation.

Example Output:
42
"""

report_generation_prompt = """
You are an expert HR analyst and recruitment specialist. Your task is to generate a comprehensive candidate assessment report based on all available data for a job application.

**Mission**
Generate a detailed, structured markdown report that evaluates the candidate's suitability for the specific role. The report should provide actionable insights for hiring managers and maintain consistent formatting.

**Core Instructions**
1. Analyze all provided data comprehensively
2. Maintain consistent markdown structure and formatting
3. Provide objective assessments with supporting evidence
4. Include specific recommendations for hiring decisions
5. IMPORTANT: Use the provided candidate name "{candidate_name}" throughout the report, do not use any other names

**Input Data**
1. Job Information:

Job Title: {job_title}
Job Description: {job_description}
Required Skills & Qualifications: {job_aspects_str}

2. Candidate Information:

Candidate Name: {candidate_name}
Full Resume Text: {resume_str}
Skills & Qualifications: {aspects_str}

3. Interview Data:

Live Interview Transcript: {transcript}

**Output Requirements**
Generate a markdown report with the following EXACT structure and formatting:

# Candidate Assessment Report

## Candidate Information
**Name:** {candidate_name}
**Position:** {job_title}

## Executive Summary
[2-3 paragraph summary of overall assessment]

## Candidate Profile
### Background
[Summary of candidate's background from resume]

### Key Strengths
- [Strength 1 with evidence]
- [Strength 2 with evidence]
- [Strength 3 with evidence]

### Areas of Concern
- [Concern 1 with evidence]
- [Concern 2 with evidence]

## Detailed Assessment

### Technical Competency
**Rating:** [High/Medium/Low]
**Analysis:** [Detailed analysis of technical skills based on resume, written interview, and live interview]

### Experience Relevance
**Rating:** [High/Medium/Low]  
**Analysis:** [Assessment of how well candidate's experience matches job requirements]

### Communication Skills
**Rating:** [High/Medium/Low]
**Analysis:** [Assessment based on written responses and interview transcript]

### Problem-Solving Ability
**Rating:** [High/Medium/Low]
**Analysis:** [Evaluation of problem-solving skills demonstrated in interviews]

### Cultural Fit
**Rating:** [High/Medium/Low]
**Analysis:** [Assessment of alignment with role expectations and team dynamics]

## Interview Performance Analysis

### Written Interview
**Performance:** [Strong/Satisfactory/Weak]
**Key Observations:**
- [Observation 1]
- [Observation 2]
- [Observation 3]

### Live Interview  
**Performance:** [Strong/Satisfactory/Weak]
**Key Observations:**
- [Observation 1]
- [Observation 2]
- [Observation 3]

## Gap Analysis
### Skills Gaps
- [Gap 1]: [Description and impact]
- [Gap 2]: [Description and impact]

### Experience Gaps
- [Gap 1]: [Description and impact]
- [Gap 2]: [Description and impact]

## Recommendations

### Hiring Decision
**Recommendation:** [Strong Hire/Hire/No Hire/Strong No Hire]

### Reasoning
[Detailed reasoning for the recommendation with supporting evidence]

### Next Steps
- [Action item 1]
- [Action item 2]
- [Action item 3]

### Onboarding Considerations
[If recommending hire, what should be considered during onboarding]

## Risk Assessment
**Overall Risk Level:** [Low/Medium/High]

### Risk Factors
- [Risk 1]: [Description and mitigation]
- [Risk 2]: [Description and mitigation]

## Conclusion
[Final paragraph summarizing the assessment and recommendation]

---
*Report generated by AI Assessment System*
*Candidate ID: {candidate_id} | Job ID: {job_id}*
"""

report_comparison_prompt = """
You are an expert HR analyst tasked with comparing two assessment reports for the same candidate to identify discrepancies, agreements, and provide a comprehensive analysis with a final screening decision.

**Job Information:**
Job Title: {job_title}
Job Description: {job_description}
Required Skills & Qualifications: {job_aspects_str}

**Reports to Compare:**

**User Report (Human Assessment):**
{user_report}

**AI Report (Automated Assessment):**
{ai_report}

**Important Note:** The data may be anonymized, so mismatching names or identifiers between reports should NOT be considered an issue or discrepancy. Focus on the actual assessment content, skills evaluation, and recommendations.

**Your Task:**
Analyze both reports and provide a detailed comparison in markdown format covering:

1. **Key Agreements**: Areas where both reports align
2. **Major Discrepancies**: Significant differences in assessment (ignore name/identifier differences)
3. **Scoring Comparison**: Compare ratings/scores if available
4. **Assessment Quality**: Evaluate the thoroughness of each report
5. **Final Recommendation**: Based on both reports, provide your consolidated recommendation
6. **Screening Decision**: Make a final decision based on alignment between reports

**Decision Logic:**
- If both reports are positive/recommend hiring → "Approved"
- If both reports are negative/recommend rejection → "Rejected"  
- If reports have conflicting recommendations → "Supervisor Required"

**Output Format:**
Provide your analysis in markdown format with clear sections and bullet points. Be objective and highlight both strengths and concerns identified in either report.

**IMPORTANT:** The very last line of your response must contain ONLY one of these three words: "Approved", "Rejected", or "Supervisor Required"

---
*Comparison Analysis for Candidate ID: {candidate_id} | Job ID: {job_id}*
"""

# Enhanced prompt that includes company policies
prompt1_with_policies = """
You are an expert recruitment AI. Your goal is to generate 12 hyper-specific, written-interview questions by analyzing a job description, a candidate's resume, and company policies.

The final output must be a valid JSON array of 12 question objects.

**Core Instructions**
1. Analyze Job, Resume & Policies:
- Identify 5-7 core competencies from the Job Information.
- Map the Candidate's Resume against these competencies.
- Review Company Policies to understand compliance requirements, cultural values, and organizational standards.
- Pinpoint specific gaps or ambiguities (e.g., a required skill is missing from the resume, unclear project scope, potential policy compliance concerns, cultural fit questions).

2. Generate Question Mix: Create a set of 12 questions with the following mix:
- Behavioral/Experience: Probe past actions and results, including policy adherence.
- Technical/Situational: Assess specific skills and future scenario handling.
- Policy/Compliance: Test understanding of company standards and ethical guidelines.
- Cultural Fit: Evaluate alignment with company values and policies.
- Gap Analysis: Constructively ask for clarification on the gaps you identified.
- Two (2) Curveballs: Insightful, non-standard questions to test creativity or problem-solving within company framework.

**Input Data**
1. Job Information:

Job Title: {job_title}
Job Description:
{job_description}

Required Skills & Qualifications:
{job_aspect_str}

2. Candidate Resume:

Full Resume Text:
{resume_str}

Skills & Qualifications:
{aspect_str}

3. Company Policies & Guidelines:

{policies_str}

**Output Requirements**
Generate a single JSON array containing exactly 12 objects. Provide no other text or explanation.

JSON Object Schema:

{{
  "question_text": "The full text of the interview question.",
  "question_type": "[Behavioral | Technical | Situational | Policy/Compliance | Cultural Fit | Gap Analysis | Curveball]",
  "objective": "A brief explanation of the competency, skill, policy understanding, or insight this question is designed to assess."
}}

**Enhanced Question Guidelines:**
- When company policies are available, incorporate 2-3 questions that test policy understanding or ethical scenarios
- Include at least 1 question about how the candidate would handle situations mentioned in company policies
- For behavioral questions, ask about past experiences that demonstrate adherence to similar standards
- Use policy context to create more realistic situational questions

Example Enhanced JSON Output Snippet:

[
  {{
    "question_text": "Your resume mentions leading a 'market analysis project' at Acme Corp. Walk me through this project, from the initial business question to your final recommendations. Detail the specific SQL queries or Python scripts you personally wrote for the analysis.",
    "question_type": "Technical",
    "objective": "Assess project management depth and verify hands-on technical proficiency in SQL/Python beyond the resume description."
  }},
  {{
    "question_text": "Based on our company's data privacy policy, describe how you would handle a situation where a stakeholder requests access to customer data that could help with their analysis but falls outside their authorized scope.",
    "question_type": "Policy/Compliance",
    "objective": "Evaluate understanding of data privacy policies and ability to balance business needs with compliance requirements."
  }},
  {{
    "question_text": "Describe a time when you had to choose between meeting a tight deadline and following proper documentation procedures. How did you handle it, and what was the outcome?",
    "question_type": "Behavioral",
    "objective": "Assess how the candidate balances competing priorities while maintaining professional standards and compliance."
  }}
]
"""

# Enhanced follow-up prompt that includes company policies
prompt2_with_policies = """
You are an expert interview strategist and senior talent assessor. Your function is to analyze a candidate's written interview responses and arm a hiring manager with a concise, tactical set of follow-up questions for a live interview, taking into account company policies and standards.

**Mission**
Your mission is to identify the most critical areas for further probing based on the candidate's written answers, job requirements, and company policies. You will generate a list of sharp, insightful follow-up questions designed to clarify vague statements, test the depth of their knowledge, explore policy understanding, and investigate their most compelling experiences in greater detail.
The final output must be a valid JSON array of follow-up question objects.

**Core Instructions**
1. Contextual Review: First, re-familiarize yourself with the Job Information, Candidate's Resume, and Company Policies to re-establish the ideal candidate profile and compliance requirements.

2. Analyze Written Responses: Scrutinize the Written Interview Transcript. For each answer, evaluate it against these criteria:
- Clarity & Specificity: Is the answer concrete and evidence-based, or is it vague and full of generalities?
- Depth: Does the answer demonstrate a deep understanding of the topic, or is it a surface-level explanation? Does it explain the "why" and "how," not just the "what"?
- Consistency: Is the answer consistent with the candidate's resume and the requirements of the job?
- Policy Alignment: Does the answer demonstrate awareness of or alignment with company standards and policies?
- Impact: Does the candidate effectively articulate the results and business impact of their actions?

3. Identify Probing Points: Based on your analysis, pinpoint the most valuable topics for a live follow-up. Prioritize:
- Vague or Generic Answers: Target statements like "I improved efficiency" or "I was part of a team" for specifics.
- High-Impact Claims: Dig into the candidate's most impressive achievements to understand their exact role and the complexity involved.
- Policy-Related Scenarios: If the candidate's answers touch on situations covered by company policies, probe their understanding and approach.
- Potential Gaps: If an answer seems to sidestep a key part of the original question, craft a question to bring the focus back.
- Technical Depth: For technical answers, prepare questions that test the boundary of their knowledge.
- Compliance Understanding: Test their grasp of relevant policies and ethical considerations.

**Input Data**
1. Job Information:

Job Title: {jobTitle}
Job Description:
{jobDesciption}

Required Skills & Qualifications:
{jobAspectStr}

2. Candidate Resume:

Full Resume Text:
{resumeStr}

Skills & Qualifications:
{aspectStr}

3. Company Policies & Guidelines:

{policies_str}

4. Written Interview Transcript:

{csv_string}

**Output Requirements**
Generate a JSON array of 8-12 follow-up question objects. Provide no other text or explanation.

JSON Object Schema:

{{
  "question_text": "The specific follow-up question to ask in the live interview.",
  "question_type": "[Technical Deep Dive | Behavioral Clarification | Policy Understanding | Scenario Exploration | Impact Verification | Gap Analysis]",
  "context": "Brief reference to which written answer or topic this follow-up addresses.",
  "objective": "What insight or clarification this question is designed to achieve."
}}

**Enhanced Follow-up Guidelines:**
- Include 1-2 policy-related follow-ups if the candidate's answers intersect with company standards
- Probe any answers that show potential policy blind spots or compliance concerns
- Create scenario-based questions that test policy application in real situations
- Balance technical depth with ethical/policy considerations where relevant

Example Enhanced JSON Output:

[
  {{
    "question_text": "You mentioned implementing a data analysis solution that improved efficiency by 25%. Can you walk me through your specific role in the technical implementation and the exact metrics you used to measure that improvement?",
    "question_type": "Technical Deep Dive",
    "context": "Response to question about data analysis project impact",
    "objective": "Verify the depth of technical involvement and accuracy of claimed metrics."
  }},
  {{
    "question_text": "In your answer about handling conflicting stakeholder requirements, you mentioned finding a compromise. Given our company's policy on data governance, how would you ensure that any compromise solution still maintains our compliance standards?",
    "question_type": "Policy Understanding",
    "context": "Response about stakeholder management and compromise solutions",
    "objective": "Test ability to balance business needs with regulatory and policy compliance."
  }}
]
"""

# Template-specific prompt for Technical Interview Assessment Report
prompt1_template_specific = """
Generate exactly 12 interview questions for a Technical Interview Assessment Report.

Job Title: {job_title}
Job Description: {job_description}
Required Skills: {job_aspect_str}
Candidate Resume: {resume_str}
Candidate Skills: {aspect_str}
Assessment Template: {policies_str}

Generate 12 questions covering:
- Technical Competency (4-5 questions): Programming Skills, System Design, Technology Stack
- Policy Compliance (2-3 questions): Data Privacy, Security, Code Quality, Documentation  
- Behavioral Assessment (3-4 questions): Communication, Collaboration, Problem-Solving, Learning
- Situational Assessment (1-2 questions): Real-world scenarios

Return ONLY a JSON array. No explanations, no markdown, no extra text.

Each question object requires these exact fields:
{{
  "question_text": "The interview question",
  "question_type": "Technical Competency",
  "assessment_area": "Programming Skills - Code Quality",
  "scoring_guidance": "Score 1-5 based on understanding of clean code principles"
}}

JSON array:"""

prompt1_customer_service_template = """
Generate exactly 12 interview questions for a Customer Service Representative Evaluation.

Job Title: {job_title}
Job Description: {job_description}
Required Skills: {job_aspect_str}
Candidate Resume: {resume_str}
Candidate Skills: {aspect_str}
Assessment Template: {policies_str}

Generate 12 questions covering:
- Customer Interaction Skills (4-5 questions): Communication, Active Listening, Empathy, Clarity
- Problem Resolution (3-4 questions): Issue Identification, Solution Finding, Follow-up, Escalation
- Company Policy Knowledge (2-3 questions): Return Policy, Warranty Guidelines, Privacy Compliance, Refund Procedures
- Soft Skills Assessment (1-2 questions): Patience, Stress Management, Multitasking, Team Cooperation

Return ONLY a JSON array. No explanations, no markdown, no extra text.

Each question object requires these exact fields:
{{
  "question_text": "The interview question",
  "question_type": "Customer Interaction Skills",
  "assessment_area": "Communication - Verbal Skills",
  "scoring_guidance": "Score 1-10 based on clarity and professionalism"
}}

JSON array:"""