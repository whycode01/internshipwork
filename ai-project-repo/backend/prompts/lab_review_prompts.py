report_generation_prompt = """Act like a Principal Architect tasked to review a project for technology leadership and maturity. A questionnaire was sent to the project team, and they have responded. Thereafter, a discussion was done with them. Based on the responses and discussion's transcript, you need to provide your observations, scope of improvement, and recommendations.

The questionnaire is divided into four sections:
1. **Technology Leadership Presence**: Evaluate the leadership's involvement, decision-making process, and communication of the technical vision.
2. **Technical Competency**: Assess the team's skills, expertise, and ability to handle the project's technical challenges.
3. **Collaboration**: Analyze the relationship between the client and the team, including conflict resolution and communication.
4. **Architecture Practice**: Review the architectural decisions, principles, and how they are communicated and adapted.

For each section, provide:
- Observations: Key findings based on the responses and transcripts.
- Scope of Improvement: Areas where the team can improve.
- Recommendations: Actionable suggestions to address the gaps.

Additionally, for each question and response, **you must assign a maturity level**:
- **High**: Perfect or near perfect.
- **Medium**: Working fine but needs attention.
- **Low**: Significant challenges exist.

For each maturity level, provide a **reason** explaining why the level was assigned.

Here is the questionnaire and response in markdown format: {responses}
Here is the transcript of conversation: {transcripts}

**Important**: Ensure that every question and response has a maturity level (High, Medium, or Low) and a reason for the assigned level.
"""

qprompt2 = """
I will provide you with two inputs:

A markdown file containing a master question bank with four sections, each filled with numerous questions.
A project description outlining the details, goals, and context of a specific project.
Your task is to:

Carefully analyze the project description to understand its key aspects.
Select "5" relevant questions from each section(namely- Technology Leadership Presence, Technical Competency, Collaboration, Architectural practices) of the master question bank that are most applicable to the project's context. You may modify the questions slightly to better fit the project if required.
Ensure the selected questions focus on important audit aspects such as compliance, security, performance, or other relevant criteria as described in the project description.
The output should be organized clearly by section, with each section's questions grouped together.

Response will also be generated in a markdown table format.

Here is the description of the project: {description}
Here is the master question bank: {question_bank}

Give me the list of questions that you want to ask the project team. Do not give any other information.
"""

# questionnare_prompt="""
# ### **Improved Prompt for Question Selection**

# I will provide you with two inputs:

# 1. **A markdown file** containing a **master question bank** with four sections:  
#    - **Technology Leadership Presence**  
#    - **Technical Competency**  
#    - **Collaboration**  
#    - **Architectural Practices**  

# 2. **A project description** outlining the details, goals, and context of a specific project.  

# ### **Your Task**
# 1. Carefully analyze the project description to understand its key aspects, goals, and potential risks.  
# 2. Select **5 relevant questions from each section** of the master question bank that are most applicable to the project's context.  
# 3. If needed, **rephrase the selected questions** to better align with the project's details while maintaining their original intent.  
# 4. Ensure the selected questions address key audit aspects such as **compliance**, **security**, **performance**, and other relevant criteria based on the project description.  
# 5. Focus on selecting questions that uncover potential risks, ensure alignment with project goals, and support best practices in implementation.  

# ### **Output Format**
# - Organize the selected questions in a **csv table** format.  
# - Group the questions by their respective sections.  
# - Each section should contain **exactly 5 questions**.  



# **Important:** Only provide the final table with no extra commentary or explanation.  

# Here is the **project description**: {description}  
# Here is the **master question bank**: {question_bank}  

# Generate the list of questions. Do not provide any additional information beyond the table.
# """

questionnare_prompt = """
give me a csv file with 20 questions from this file {question_bank} based on this description {description}
5 questions each from the following sections:
- Technology Leadership Presence
- Technical Competency
- Collaboration
- Architectural Practices

Donot include any extra information, only provide the 5 questions from each section in csv format clubbed together.
"""


cross_questionnaire_prompt = """
I will provide you with a csv file containing questions and responses.
Your task is to generate cross questions based on the provided questions and responses and return a csv file.

For each question and response pair, you need to create a cross question that further explores the topic or seeks additional information. The cross questions should be relevant, insightful, and demonstrate a deep understanding of the subject matter.
The cross questions should be logically connected to the original question and response, building upon the information provided.

The output should be organized clearly, with each original question, response, and corresponding cross question presented together.

Here is the csv file containing questions and responses: {questions_responses}
Donot include any extra information like here is the output: etc, directly start with the content, only provide the question, response pair with cross-questions in csv format. Donot provide reponses for the cross questions.
"""