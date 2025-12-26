/* eslint-disable react/prop-types */
/* eslint-disable no-unused-vars */
import { createContext, useContext, useState } from 'react';

// Define different label sets
const labelSets = {
    audit: {
        dashboard_word: "domain",
        dashboard_title: "Domains",
        dashboard_create_new: "Create New Domain",
        dashboard_form_title: "Domain Name",
        dashboard_edit_title: "Edit Domain",
        dashboard_edit_inp1: "Domain Name",
        dashboard_edit_btn: "Update Domain",
        dashboard_new_title: "Create A New Domain",
        dashboard_new_inp1: "Domain Name",
        dashboard_new_btn: "Create Domain",
        dashboard_new_t1: "📋 Domain Name:",
        dashboard_new_l1: "Choose a broad area of your organization",
        dashboard_new_t2: "📝 Description:",
        dashboard_new_l2: "Explain what this domain covers and why it's important for your organization.",
        dashboard_new_t3: "🎯 Aspects:",
        dashboard_new_l3: "Break down the domain into major categories or areas of focus",
        dashboard_new_t4: "🔍 Focus Areas:",
        dashboard_new_l4: "Specific topics or activities within each aspect",
        dashboard_dlt_title: "Delete Domain",
        dashboard_empty: "domains",
        dashboard_empty_first: "domain",

        list_title: "Labs Dasboard",
        list_btn: "New Lab",
        list_err: "labs",
        list_col1: "Lab ID",
        list_col2: "Name",

        new_title: "Lab",

        view_word: "lab",
        view_l_title: "Lab Information",
        view_l_btn: "Download Report",
        view_r_title: "Lab Management",
        view_r_btn1_gn: "Generate Questionnaire",
        view_r_btn1_dl: "Download Interview Questions",
        view_r_btn2_gn: "Generate Cross Questions",
        view_r_btn2_dl: "Download Cross Questions",
        view_r_btn3: "Get Transcript",
    },
    job: {
        dashboard_word: "job",
        dashboard_title: "Job Descriptions",
        dashboard_create_new: "Create New Job",
        dashboard_form_title: "Job Title",
        dashboard_edit_title: "Edit Job Description",
        dashboard_edit_inp1: "Job Title",
        dashboard_edit_btn: "Update Job Description",
        dashboard_new_title: "Create A New Job Description",
        dashboard_new_inp1: "Job Title",
        dashboard_new_btn: "Create Job Description",
        dashboard_new_t1: "💼 Job Title:",
        dashboard_new_l1: "Enter a specific job title or role",
        dashboard_new_t2: "📝 Job Description:",
        dashboard_new_l2: "Provide a detailed description of the role's responsibilities and expectations.",
        dashboard_new_t3: "🎯 Job Requirements:",
        dashboard_new_l3: "Break down the job into major requirement categories",
        dashboard_new_t4: "🔍 Specific Details:",
        dashboard_new_l4: "Specific requirements or skills within each category",
        dashboard_dlt_title: "Delete Job",
        dashboard_empty: "job descriptions",
        dashboard_empty_first: "job description",

        list_title: "Candidates Dasboard",
        list_btn: "New Candidate",
        list_err: "candidates",
        list_col1: "Cand. ID",
        list_col2: "Full Name",

        new_title: "Candidate",

        view_word: "candidate",
        view_l_title: "Candidate Information",
        view_l_btn: "Download Resume",
        view_r_title: "Interview Management",
        view_r_btn1_gn: "Generate Interview Questions",
        view_r_btn1_dl: "Download Interview Questions",
        view_r_btn2_gn: "Get Interview Transcript",
        view_r_btn2_dl: "Download Automated Report",
        view_r_btn3: "Get Transcript",
    },
};

// Create Context
const LabelsContext = createContext(null);

// Context Provider Component
export const LabelsProvider = ({ children }) => {
    const [labels, setLabels] = useState(labelSets.audit); // Default: Audit Process

    // Function to switch labels dynamically
    const switchLabels = (type) => {
        setLabels(labelSets[type] || labelSets.audit);
    };

    return (
        <LabelsContext.Provider value={{ labels, switchLabels }}>
            {children}
        </LabelsContext.Provider>
    );
};

export const useLabels = () => useContext(LabelsContext);
