/* eslint-disable no-unused-vars */
import axios from 'axios';
import { Calendar, ChevronDown, Download, FileText, Loader2, Mail, Phone, SquarePen, Upload, User } from 'lucide-react';
import { useCallback, useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useLabels } from '../context/LabelsContext.jsx';
import TranscriptManager from './TranscriptManager.jsx';

const API_BASE_URL_AUD = 'http://localhost:8000/api/audit';
const API_BASE_URL_JOB = 'http://localhost:8000/api/jobs';
const API_BASE_URL_POLICIES = 'http://localhost:8000/api/policies';

function J_Candidates_Screening() {
    const navigate = useNavigate();
    const location = useLocation();
    const { labels, switchLabels } = useLabels();
    
    const [currentCandidate, setCurrentCandidate] = useState(null);
    const [currentJob, setCurrentJob] = useState(null);
    const [message, setMessage] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [mainId, setMainId] = useState('');
    const [subId, setSubId] = useState('');
    const [isPolling, setIsPolling] = useState(false);
    const [isCrossPolling, setIsCrossPolling] = useState(false);
    const [isFinalPolling, setIsFinalPolling] = useState(false);
    const [showTranscriptManager, setShowTranscriptManager] = useState(false);
    
    // Policy and template selection states
    const [availablePolicies, setAvailablePolicies] = useState([]);
    const [availableReportTemplates, setAvailableReportTemplates] = useState([]);
    const [selectedPolicyId, setSelectedPolicyId] = useState('');
    const [selectedReportTemplateId, setSelectedReportTemplateId] = useState('');
    const [loadingPolicies, setLoadingPolicies] = useState(false);
    const [showPolicySelection, setShowPolicySelection] = useState(false);
    const [showReportTemplateSelection, setShowReportTemplateSelection] = useState(false);

    // Refs to avoid dependency issues in useCallback
    const pollingStateRef = useRef({ isPolling: false, isCrossPolling: false, isFinalPolling: false });
    const isAuditRef = useRef(location.pathname.startsWith('/audit'));
    
    // State that depends on location
    const [isAudit, setIsAudit] = useState(location.pathname.startsWith('/audit'));
    
    // Update refs when states change
    useEffect(() => {
        pollingStateRef.current = { isPolling, isCrossPolling, isFinalPolling };
    }, [isPolling, isCrossPolling, isFinalPolling]);
    
    useEffect(() => {
        isAuditRef.current = isAudit;
    }, [isAudit]);

    const AUDIT_STATUS_ORDER = {
        "Lab Created": 0,
        "Questionnare Error": 1,
        "Generating Questionnare": 2,
        "Generated Questionnaire": 3,
        "Followup Initiated": 4,
        "Cross Questions Error": 5,
        "Generating Cross Questions": 6,
        "Generated Cross Questions": 7,
        "Report Error": 8,
        "Generating Report": 9,
        "Generated Report": 10
    };

    const JOB_STATUS_ORDER = {
        "New": 0,
        "Questions Error": 1,
        "Generating Questions": 2,
        "Generated Questions": 3, // TILL HERE IS DONE
        "Error Generating Report": 4,
        "Generating Report": 5,
        "Generated Report": 6,
        "Error Comparing Reports": 7,
        "Comparing Reports": 8,
        "Compared Reports": 9,
        "Awaiting Supervisor Decision": 10,
        "Rejected": 11,
        "Accepted": 12,
    };

    const auditStatusOrder = AUDIT_STATUS_ORDER[currentCandidate?.status] ?? -1;
    const jobStatusOrder = JOB_STATUS_ORDER[currentCandidate?.status] ?? -1;

    // Define fetch functions before using them in useEffect hooks
    const fetchJobDetails = useCallback(async (mId) => {
        setIsLoading(true);
        try {
            const currentIsAudit = isAuditRef.current;
            const API_URL = currentIsAudit
                ? `${API_BASE_URL_AUD}/domains/${mId}`
                : `${API_BASE_URL_JOB}/descriptions/${mId}`;
            const response = await axios.get(API_URL);

            if (response.data == null) {
                if (currentIsAudit) {
                    navigate(`/audit`);
                } else {
                    navigate(`/jobs`);
                }
            } else {
                setCurrentJob(response.data);
            }
        } catch (error) {
            console.error('Error fetching job details:', error);
            setMessage('Error loading job details');
        } finally {
            setIsLoading(false);
        }
    }, [navigate]); // Removed isAudit dependency

    const fetchSubDetails = useCallback(async (mId, sId) => {
        const { isPolling: currentIsPolling, isCrossPolling: currentIsCrossPolling, isFinalPolling: currentIsFinalPolling } = pollingStateRef.current;
        const currentIsAudit = isAuditRef.current;
        const shouldShowLoading = !currentIsPolling && !currentIsCrossPolling && !currentIsFinalPolling;
        
        if (shouldShowLoading) {
            setIsLoading(true);
        }

        try {
            const API_URL = currentIsAudit
                ? `${API_BASE_URL_AUD}/labs/${mId}/${sId}`
                : `${API_BASE_URL_JOB}/candidates/${mId}/${sId}`;
            const response = await axios.get(API_URL);

            if (response.data == null) {
                if (currentIsAudit) {
                    navigate(`/audit/labs?domainId=${mId}`)
                } else {
                    navigate(`/jobs/candidates?jobId=${mId}`)
                }
            } else {
                setCurrentCandidate(response.data);
            }
        } catch (error) {
            console.error('Error fetching candidate details:', error);
            setMessage('Error loading candidate details');
        } finally {
            if (shouldShowLoading) {
                setIsLoading(false);
            }
        }
    }, [navigate]); // Removed isAudit dependency completely

    // Load policies and report templates function
    const loadPolicies = useCallback(async () => {
        try {
            setLoadingPolicies(true);
            
            // Load both policies and report templates separately
            const [policiesResponse, templatesResponse] = await Promise.all([
                axios.get(`${API_BASE_URL_POLICIES}/policies`),
                axios.get(`${API_BASE_URL_POLICIES}/report_templates`)
            ]);
            
            // Set policies for question generation
            if (policiesResponse.data.success) {
                setAvailablePolicies(policiesResponse.data.data);
                setShowPolicySelection(policiesResponse.data.data.length > 0);
            } else {
                setAvailablePolicies([]);
                setShowPolicySelection(false);
            }
            
            // Set report templates for report generation
            if (templatesResponse.data.success) {
                setAvailableReportTemplates(templatesResponse.data.data);
                setShowReportTemplateSelection(templatesResponse.data.data.length > 0);
            } else {
                setAvailableReportTemplates([]);
                setShowReportTemplateSelection(false);
            }
            
        } catch (error) {
            console.error('Error loading policies and templates:', error);
            setShowPolicySelection(false);
            setShowReportTemplateSelection(false);
        } finally {
            setLoadingPolicies(false);
        }
    }, []);

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        const currentIsAudit = location.pathname.startsWith('/audit');
        setIsAudit(currentIsAudit);

        const mainIdParam = currentIsAudit
            ? queryParams.get('domainId')
            : queryParams.get('jobId');
        const subIdParam = currentIsAudit
            ? queryParams.get('labId')
            : queryParams.get('candidateId');

        if (mainIdParam && subIdParam) {
            switchLabels(currentIsAudit
                ? 'audit'
                : 'job');
            setMainId(mainIdParam)
            setSubId(subIdParam);
        } else {
            if (mainIdParam) {
                if (currentIsAudit) {
                    navigate(`/audit/labs?domainId=${mainIdParam}`);
                } else {
                    navigate(`/jobs/candidates?jobId=${mainIdParam}`);
                }
            } else {
                if (currentIsAudit) {
                    navigate(`/audit/`);
                } else {
                    navigate(`/jobs/`);
                }
            }
            setIsLoading(false);
        }
    }, [location.pathname, location.search, navigate, switchLabels]);

    // Separate useEffect to handle data fetching when IDs change
    useEffect(() => {
        if (mainId && subId) {
            fetchJobDetails(mainId);
            fetchSubDetails(mainId, subId);
        }
    }, [mainId, subId, fetchJobDetails, fetchSubDetails]); // Functions should now be stable

    useEffect(() => {
        let intervalId;

        if (isPolling && mainId && subId) {
            intervalId = setInterval(() => {
                fetchSubDetails(mainId, subId);
            }, 2000); // Poll Every 2s
        }

        return () => {
            if (intervalId) {
                clearInterval(intervalId);
                if (isPolling) fetchSubDetails(mainId, subId);
            }
        };
    }, [isPolling, fetchSubDetails, mainId, subId]);

    useEffect(() => {
        let crossIntervalId;

        if (isCrossPolling && subId && mainId) {
            crossIntervalId = setInterval(() => {
                fetchSubDetails(mainId, subId);
            }, 2000); // Poll Every 2s
        }

        return () => {
            if (crossIntervalId) {
                clearInterval(crossIntervalId);
            }
        };
    }, [isCrossPolling, fetchSubDetails, mainId, subId]);

    useEffect(() => {
        let finalIntervalId;

        if (isFinalPolling && subId && mainId) {
            finalIntervalId = setInterval(() => {
                fetchSubDetails(mainId, subId);
            }, 2000); // Poll Every 2s
        }

        return () => {
            if (finalIntervalId) {
                clearInterval(finalIntervalId);
            }
        };
    }, [isFinalPolling, fetchSubDetails, mainId, subId]);

    useEffect(() => {
        if (!currentCandidate) return;

        if (!isPolling && ((isAudit && currentCandidate?.status === "Generating Questionnare") || (!isAudit && currentCandidate?.status === "Generating Questions"))) {
            setIsPolling(true);
        } else if (!isCrossPolling && ((isAudit && currentCandidate?.status === "Generating Cross Questions") || (!isAudit && currentCandidate?.status === "Generating Report"))) {
            setIsCrossPolling(true);
        } else if (!isFinalPolling && ((isAudit && currentCandidate?.status === "Generating Report") || (!isAudit && currentCandidate?.status === "Comparing Reports"))) {
            setIsFinalPolling(true);
        }

        if (
            isPolling &&
            currentCandidate.status &&
            (
                (isAudit && (currentCandidate.status === "Generated Questionnaire" || currentCandidate.status === "Questionnare Error")) ||
                (!isAudit && (currentCandidate.status === "Generated Questions" || currentCandidate.status === "Questions Error"))
            )
        ) {
            setIsPolling(false);
            if (currentCandidate.status.startsWith("Generated Question") || currentCandidate.status === "Generated Questionnaire") {
                setMessage("Question generation complete");
            } else if (currentCandidate.status.includes("Error")) {
                setMessage("Error generating questions. Please try again.");
            }
            setTimeout(() => setMessage(''), 3000);
        } else if (
            isCrossPolling &&
            currentCandidate.status &&
            (
                (isAudit && (currentCandidate.status === "Generated Cross Questions" || currentCandidate.status === "Cross Questions Error")) ||
                (!isAudit && (currentCandidate.status === "Generated Report" || currentCandidate.status === "Error Generating Report"))
            )
        ) {
            setIsCrossPolling(false);
            if (currentCandidate.status === "Generated Cross Questions") {
                setMessage("Cross questions generation complete");
            } else if (currentCandidate.status === "Cross Questions Error") {
                setMessage("Error generating cross questions. Please try again.");
            } else if (currentCandidate.status === "Generated Report") {
                setMessage("Report generated successfully. Starting comparison...");
                setIsFinalPolling(true); // Start final polling for comparison results
            } else if (currentCandidate.status === "Error Generating Report") {
                setMessage("Error generating report. Please try again.");
            }
            setTimeout(() => setMessage(''), 3000);
        } else if (
            isFinalPolling &&
            currentCandidate.status &&
            (
                (isAudit && (currentCandidate.status === "Generated Report" || currentCandidate.status === "Report Error")) ||
                (!isAudit && (currentCandidate.status === "Error Comparing Reports" || currentCandidate.status === "Awaiting Supervisor Decision" || currentCandidate.status === "Rejected" || currentCandidate.status === "Accepted"))
            )
        ) {
            setIsFinalPolling(false);
            if (currentCandidate.status === "Generated Report") {
                setMessage("Report generation complete");
            } else if (currentCandidate.status === "Report Error") {
                setMessage("Error generating report. Please try again.");
            } else if (currentCandidate.status === "Error Comparing Reports") {
                setMessage("Error comparing reports. Please try again.");
            } else if (currentCandidate.status === "Awaiting Supervisor Decision") {
                setMessage("Awaiting supervisor decision");
            } else if (currentCandidate.status === "Rejected") {
                setMessage("Candidate rejected");
            } else if (currentCandidate.status === "Accepted") {
                setMessage("Candidate accepted");
            }
            setTimeout(() => setMessage(''), 3000);
        }
    }, [currentCandidate, isPolling, isCrossPolling, isFinalPolling, location.pathname, isAudit]);

    const handleDownloadResume = () => {
        if (isAudit) {
            if (currentCandidate?.id) {
                axios.get(`${API_BASE_URL_AUD}/reports/${mainId}/${subId}`)
                    .then(response => {
                        // Parse JSON and get .reports[0].report
                        const data = response.data;
                        if (data && data.reports && data.reports.length > 0 && data.reports[0].report) {
                            const reportContent = data.reports[0].report;
                            const filename = `lab_report_${currentCandidate.name}.md`;
                            const blob = new Blob([reportContent], { type: 'text/markdown' });
                            const url = window.URL.createObjectURL(blob);
                            const link = document.createElement('a');
                            link.href = url;
                            link.setAttribute('download', filename);
                            document.body.appendChild(link);
                            link.click();
                            link.parentNode.removeChild(link);
                            window.URL.revokeObjectURL(url);
                        } else {
                            setMessage('No report found to download.');
                        }
                    })
                    .catch(error => {
                        setMessage('Error downloading report. Please try again.');
                        console.error('Error downloading report:', error);
                    });
            }
        } else {
            if (currentCandidate?.resume) {
                window.open(currentCandidate.resume, '_blank');
            }
        }
    };

    const handleGenerateQuestions = async () => {
        try {
            setIsPolling(true);
            
            // Build the request URL and data
            const API_URL = isAudit
                ? `${API_BASE_URL_AUD}/questions/${mainId}/${subId}`
                : `${API_BASE_URL_JOB}/questions/${mainId}/${subId}`;
            
            // Include selected policy ID in the request if available
            const requestData = {};
            if (!isAudit && selectedPolicyId) {
                requestData.policyId = selectedPolicyId;
            }

            const response = await axios.post(API_URL, requestData);

            if (response.data) {
                setMessage(response.data.message);
            } else {
                setIsPolling(false);
            }
        } catch (error) {
            setIsPolling(false);
            console.error('Error generating interview questions:', error);
            setMessage('Error generating interview questions. Please try again.');
        }
    };

    // Load policies when component mounts (only for job interviews)
    useEffect(() => {
        if (!isAudit) {
            loadPolicies();
        }
    }, [isAudit, loadPolicies]);

    const handleDownloadQuestions = async () => {
        try {
            const API_URL = isAudit
                ? `${API_BASE_URL_AUD}/questions/${mainId}/${subId}`
                : `${API_BASE_URL_JOB}/questions/${mainId}/${subId}`
            // Get Questions Data
            const response = await axios.get(API_URL);

            if (response.data && (response.data.questions_csv || response.data.report)) {
                // Create Blob From CSV Content
                const blob = new Blob([isAudit ? response.data.report : response.data.questions_csv], {
                    type: 'text/csv;charset=utf-8'
                });

                // Create Download Link
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                let fileName = isAudit ? `lab_questions_${currentCandidate.name}.csv` : `interview_questions_${currentCandidate.full_name}.csv`;
                link.setAttribute('download', fileName);
                document.body.appendChild(link);
                link.click();

                // Cleanup
                link.parentNode.removeChild(link);
                window.URL.revokeObjectURL(url);
            } else if (response.data && response.data.error) {
                setMessage(response.data.error);
            } else {
                setMessage('No questions available for download.');
            }
        } catch (error) {
            console.error('Error downloading interview questions:', error);
            if (error.response && error.response.data && error.response.data.error) {
                setMessage(error.response.data.error);
            } else {
                setMessage('Error downloading interview questions. Please try again.');
            }
        }
    };

    const handleGenerateCrossQuestions = () => {
        if (isAudit) {
            // For audit: Keep existing file upload for CSV
            const fileInput = document.createElement('input');
            fileInput.type = 'file';
            fileInput.accept = '.csv';
            fileInput.style.display = 'none';

            fileInput.onchange = async (e) => {
                const file = e.target.files[0];
                if (!file) return;

                try {
                    setIsCrossPolling(true);
                    const formData = new FormData();
                    
                    setMessage('Starting cross questions generation...');
                    formData.append('csv_file', file);
                    const API_URL = `${API_BASE_URL_AUD}/cross-questions/${mainId}/${subId}`;

                    const response = await axios.post(
                        API_URL,
                        formData,
                        { headers: { 'Content-Type': 'multipart/form-data' } }
                    );

                    if (response.data && response.data.message) {
                        setMessage(response.data.message);
                    } else {
                        setIsCrossPolling(false);
                        setMessage('Error starting cross questions generation');
                    }
                } catch (error) {
                    setIsCrossPolling(false);
                    setMessage('Error generating cross questions. Please try again.');
                    console.error(error);
                }
            };

            document.body.appendChild(fileInput);
            fileInput.click();
            document.body.removeChild(fileInput);
        } else {
            // For jobs: Open the transcript manager modal
            setShowTranscriptManager(true);
        }
    };

    const handleDownloadCrossQuestions = async () => {
        if (isAudit) {

            try {
                const API_URL = `${API_BASE_URL_AUD}/cross-questions/${mainId}/${subId}`;
                const response = await axios.get(API_URL);

                if (response.data && response.data.report) {
                    // Create Blob From CSV Content
                    const blob = new Blob([response.data.report], {
                        type: 'text/csv;charset=utf-8'
                    });

                    // Create Download Link
                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `cross_questions_${currentCandidate.name}.csv`);
                    document.body.appendChild(link);
                    link.click();

                    // Cleanup
                    link.parentNode.removeChild(link);
                    window.URL.revokeObjectURL(url);
                } else if (response.data && response.data.error) {
                    setMessage(response.data.error);
                } else {
                    setMessage('No cross questions available for download.');
                }
            } catch (error) {
                console.error('Error downloading cross questions:', error);
                if (error.response && error.response.data && error.response.data.error) {
                    setMessage(error.response.data.error);
                } else {
                    setMessage('Error downloading cross questions. Please try again.');
                }
            }
        } else {
            try {
                const API_URL = `${API_BASE_URL_JOB}/ai-report/${mainId}/${subId}`;
                const response = await axios.get(API_URL);

                if (response.data && response.data.ai_report) {
                    const blob = new Blob([response.data.ai_report], {
                        type: 'text/markdown;charset=utf-8'
                    });

                    const url = window.URL.createObjectURL(blob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.setAttribute('download', `ai_report_${currentCandidate?.full_name || 'candidate'}.md`);
                    document.body.appendChild(link);
                    link.click();

                    link.parentNode.removeChild(link);
                    window.URL.revokeObjectURL(url);
                } else {
                    setMessage('No AI report available for download.');
                }
            } catch (error) {
                console.error('Error downloading AI report:', error);
                if (error.response && error.response.data && error.response.data.error) {
                    setMessage(error.response.data.error);
                } else {
                    setMessage('Error downloading AI report. Please try again.');
                }
            }
        }

    };

    const handleTranscriptFetched = () => {
        if (isAudit) {
            // For audit: Start final polling when transcript is submitted for report generation
            setIsFinalPolling(true);
            setMessage('Report generation started with fetched transcript');
        } else {
            // For jobs: Start cross polling when transcript is submitted for report generation
            setIsCrossPolling(true);
            setMessage('Report generation started with fetched transcript');
        }
        setTimeout(() => setMessage(''), 3000);
    };

    const renderAspects = () => {
        if (!currentCandidate?.aspects || currentCandidate.aspects.length === 0) {
            return <p className="text-gray-500">No skills/aspects specified</p>;
        }

        return (
            <div className="space-y-4">
                {currentCandidate.aspects.map((aspect, index) => (
                    <div key={index} className="border rounded-lg p-4 bg-gray-50">
                        <h4 className="font-semibold text-lg mb-2">{aspect.name}</h4>
                        {aspect.focusAreas && aspect.focusAreas.length > 0 ? (
                            <div className="flex flex-wrap gap-2">
                                {aspect.focusAreas.map((skill, skillIndex) => (
                                    <span
                                        key={skillIndex}
                                        className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm"
                                    >
                                        {skill}
                                    </span>
                                ))}
                            </div>
                        ) : (
                            <p className="text-gray-500 text-sm">No specific skills listed</p>
                        )}
                    </div>
                ))}
            </div>
        );
    };

    if (isLoading) {
        return (
            <div className="p-6 flex flex-col items-center justify-center h-screen">
                <div className="flex items-center justify-center">
                    <Loader2 className="animate-spin mr-2" size={24} />
                    <span>Loading {labels.view_word} details...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-white flex flex-col items-center justify-start py-10 px-2">
            {/* Header */}
            <div className="w-full max-w-5xl flex flex-row justify-between items-start mb-6">
                <div>
                    <h1 className="text-4xl font-bold text-gray-900">
                        {currentCandidate?.full_name || currentCandidate?.name}
                    </h1>
                    <p className="text-lg text-gray-500 mt-1">
                        {currentJob?.name}
                    </p>
                </div>
            </div>

            {/* Main Content: Two Cards Side by Side */}
            <div className="w-full max-w-5xl flex flex-col md:flex-row gap-8 md:gap-10">
                {/* Candidate Information Card */}
                <div className="flex-1 bg-white rounded-xl shadow border p-8 min-w-[320px] flex flex-col justify-between">
                    <div>
                        <div className="flex items-center mb-4 relative">
                            <User className="w-5 h-5 text-gray-700" />
                            <span className="font-semibold text-lg ml-2">{labels.view_l_title}</span>
                            <span className="absolute right-0 top-1/2 -translate-y-1/2">
                                <SquarePen
                                    className="w-5 h-5 text-gray-700 hover:text-blue-600 cursor-pointer"
                                    onClick={() => navigate(`/jobs/candidates/edit?jobId=${mainId}&candidateId=${subId}`)}
                                    title="Edit candidate"
                                />
                            </span>
                        </div>
                        <hr className="mb-4" />
                        <div className="space-y-4">
                            {/* Mail */}
                            {currentCandidate?.email && currentCandidate.email.trim() !== '' && (
                                <>
                                    <div className="flex items-center gap-2 text-gray-700">
                                        <Mail className="w-4 h-4" />
                                        <span>Email</span>
                                    </div>
                                    <div className="ml-7 text-gray-900 font-medium">
                                        {currentCandidate?.email || 'N/A'}
                                    </div>
                                </>
                            )}
                            {/* Phone */}
                            {currentCandidate?.phone_number && currentCandidate.phone_number.trim() !== '' && (
                                <>
                                    <div className="flex items-center gap-2 text-gray-700 mt-2">
                                        <Phone className="w-4 h-4" />
                                        <span>Phone</span>
                                    </div>
                                    <div className="ml-7 text-gray-900 font-medium">
                                        {currentCandidate.phone_number}
                                    </div>
                                </>
                            )}
                            
                            {/* Assessment Scores Section - Only show for job interviews with scores */}
                            {!isAudit && (currentCandidate?.final_score !== null && currentCandidate?.final_score !== undefined) && (
                                <div className="mt-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
                                    <div className="flex items-center gap-2 text-blue-800 mb-3">
                                        <FileText className="w-4 h-4" />
                                        <span className="font-semibold">Assessment Scores</span>
                                    </div>
                                    
                                    {/* Final Score and Decision */}
                                    <div className="mb-3">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-gray-700">Final Score</span>
                                            <span className="text-lg font-bold text-blue-700">
                                                {Math.round(currentCandidate.final_score)}/100
                                            </span>
                                        </div>
                                        {currentCandidate?.decision && (
                                            <div className="flex justify-between items-center mt-1">
                                                <span className="text-sm font-medium text-gray-700">Decision</span>
                                                <span className={`text-sm font-semibold px-2 py-1 rounded ${
                                                    currentCandidate.decision === 'SELECTED' ? 'bg-green-100 text-green-800' :
                                                    currentCandidate.decision === 'CONDITIONAL' ? 'bg-yellow-100 text-yellow-800' :
                                                    currentCandidate.decision === 'UNDER_REVIEW' ? 'bg-blue-100 text-blue-800' :
                                                    'bg-red-100 text-red-800'
                                                }`}>
                                                    {currentCandidate.decision.replace('_', ' ')}
                                                </span>
                                            </div>
                                        )}
                                    </div>
                                    
                                    {/* Individual Scores */}
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        {currentCandidate?.technical_score !== null && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Technical:</span>
                                                <span className="font-medium">{Math.round(currentCandidate.technical_score * 10)}/100</span>
                                            </div>
                                        )}
                                        {currentCandidate?.behavioral_score !== null && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Behavioral:</span>
                                                <span className="font-medium">{Math.round(currentCandidate.behavioral_score * 10)}/100</span>
                                            </div>
                                        )}
                                        {currentCandidate?.experience_score !== null && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Experience:</span>
                                                <span className="font-medium">{Math.round(currentCandidate.experience_score * 10)}/100</span>
                                            </div>
                                        )}
                                        {currentCandidate?.cultural_score !== null && (
                                            <div className="flex justify-between">
                                                <span className="text-gray-600">Cultural:</span>
                                                <span className="font-medium">{Math.round(currentCandidate.cultural_score * 10)}/100</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                            
                            <div className="flex items-center gap-2 text-gray-700 mt-2">
                                <FileText className="w-4 h-4" />
                                <span>Status</span>
                            </div>
                            {/* Status */}
                            <div className="ml-7">
                                {currentCandidate?.status ? (
                                    <span className={`inline-block px-3 py-1 text-xs font-semibold rounded-full ${
                                        currentCandidate.status.includes('LangGraph') ? 'bg-purple-100 text-purple-700' :
                                        currentCandidate.status.includes('SELECTED') ? 'bg-green-100 text-green-700' :
                                        currentCandidate.status.includes('REJECTED') ? 'bg-red-100 text-red-700' :
                                        currentCandidate.status.includes('Error') ? 'bg-red-100 text-red-700' :
                                        currentCandidate.status.includes('Generating') ? 'bg-yellow-100 text-yellow-700' :
                                        'bg-blue-100 text-blue-700'
                                    }`}>
                                        {currentCandidate.status}
                                    </span>
                                ) : 'N/A'}
                            </div>
                            {/* Application Date */}
                            <div className="flex items-center gap-2 text-gray-700 mt-2">
                                <Calendar className="w-4 h-4" />
                                <span>Created At</span>
                            </div>
                            <div className="ml-7 text-gray-900 font-medium">
                                {currentCandidate && currentCandidate.created_at
                                    ? new Date(currentCandidate.created_at).toLocaleDateString()
                                    : 'N/A'}
                            </div>
                        </div>
                    </div>
                    <div className="mt-auto pt-8">
                        <hr className="mb-6" />
                        {
                            isAudit ? (
                                <button
                                    className="w-full flex items-center justify-center gap-2 border border-gray-300 rounded-lg px-4 py-2 font-semibold text-gray-700 hover:bg-gray-100 transition"
                                    onClick={handleDownloadResume}
                                >
                                    <Download className="w-4 h-4" /> {labels.view_l_btn}
                                </button>
                            ) : <></>
                        }

                    </div>
                </div>

                {/* Interview Management Card */}
                <div className="flex-1 bg-white rounded-xl shadow border p-8 min-w-[320px] flex flex-col justify-between">
                    <div className="flex flex-col h-full">
                        <div>
                            <div className="flex items-center gap-2 mb-4">
                                <FileText className="w-5 h-5 text-gray-700" />
                                <span className="font-semibold text-lg">{labels.view_r_title}</span>
                            </div>
                            <hr className="mb-4" />
                            
                            {/* Policy Selection (only for job interviews) */}
                            {!isAudit && showPolicySelection && (
                                <div className="mb-6">
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        Select Policy for Question Generation
                                    </label>
                                    <div className="relative">
                                        <select
                                            value={selectedPolicyId}
                                            onChange={e => setSelectedPolicyId(e.target.value)}
                                            className="border border-gray-300 p-3 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white text-gray-900 font-medium text-sm"
                                            disabled={loadingPolicies}
                                        >
                                            <option value="">All Available Policies</option>
                                            {availablePolicies.map(policy => (
                                                <option key={policy.id} value={policy.id}>
                                                    {policy.name}
                                                </option>
                                            ))}
                                        </select>
                                        <span className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                                            {loadingPolicies ? (
                                                <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
                                            ) : (
                                                <ChevronDown className="h-4 w-4 text-gray-400" />
                                            )}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {selectedPolicyId 
                                            ? "Questions will be tailored to the selected policy" 
                                            : "Questions will consider all available policies"
                                        }
                                    </p>
                                </div>
                            )}
                            
                            {/* Report Template Selection (only for job interviews) */}
                            {!isAudit && showReportTemplateSelection && (
                                <div className="mb-6">
                                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                                        Select Report Template for Report Generation
                                    </label>
                                    <div className="relative">
                                        <select
                                            value={selectedReportTemplateId}
                                            onChange={e => setSelectedReportTemplateId(e.target.value)}
                                            className="border border-gray-300 p-3 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-green-500 focus:border-green-500 appearance-none bg-white text-gray-900 font-medium text-sm"
                                            disabled={loadingPolicies}
                                        >
                                            <option value="">Default Report Format</option>
                                            {availableReportTemplates.map(template => (
                                                <option key={template.id} value={template.id}>
                                                    {template.name}
                                                </option>
                                            ))}
                                        </select>
                                        <span className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                                            {loadingPolicies ? (
                                                <Loader2 className="h-4 w-4 text-gray-400 animate-spin" />
                                            ) : (
                                                <ChevronDown className="h-4 w-4 text-gray-400" />
                                            )}
                                        </span>
                                    </div>
                                    <p className="text-xs text-gray-500 mt-1">
                                        {selectedReportTemplateId 
                                            ? "Report will follow the selected template structure" 
                                            : "Report will use default format"
                                        }
                                    </p>
                                </div>
                            )}
                            
                            {/* Interview Questions Group */}
                            <div className="flex flex-col gap-3 mb-4 pt-7">
                                <button
                                    className={`flex items-center gap-2 bg-black hover:bg-gray-900 text-white font-semibold px-4 py-2 rounded-lg transition w-full ${isLoading || isPolling || (isAudit && auditStatusOrder >= 9) || (!isAudit && jobStatusOrder >= 6) ? 'opacity-70 cursor-not-allowed' : ''}`}
                                    onClick={handleGenerateQuestions}
                                    disabled={isLoading || isPolling || (isAudit && auditStatusOrder >= 9) || (!isAudit && jobStatusOrder >= 6)}
                                >
                                    {isLoading || isPolling || currentCandidate?.status.startsWith("Generating Question") ? (
                                        <Loader2 className="animate-spin w-4 h-4" />
                                    ) : (
                                        <FileText className="w-4 h-4" />
                                    )}
                                    {labels.view_r_btn1_gn}
                                </button>
                                <button
                                    className={`flex items-center gap-2 border border-gray-300 rounded-lg px-4 py-2 font-semibold text-gray-700 hover:bg-gray-100 transition w-full ${isLoading || isPolling || (currentCandidate?.status === "New" || currentCandidate?.status === "Lab Created" || currentCandidate?.status.startsWith("Generating Question") || currentCandidate?.status === "Questionnare Error" || currentCandidate?.status === "Questions Error") ? 'opacity-70 cursor-not-allowed' : ''}`}
                                    onClick={handleDownloadQuestions}
                                    disabled={isLoading || isPolling || (isAudit && auditStatusOrder < 3) || (!isAudit && jobStatusOrder < 3)}
                                >
                                    {isLoading || isPolling || currentCandidate?.status.startsWith("Generating Question") ? (
                                        <Loader2 className="animate-spin w-4 h-4" />
                                    ) : (
                                        <Download className="w-4 h-4" />
                                    )}
                                    {labels.view_r_btn1_dl}
                                </button>
                            </div>
                            {/* Cross Questions Group */}
                            <div className="flex flex-col gap-3 mb-4 pt-7">
                                <button
                                    className={`flex items-center gap-2 bg-black hover:bg-gray-900 text-white font-semibold px-4 py-2 rounded-lg transition w-full ${
                                        isLoading || isCrossPolling || 
                                        (isAudit && (auditStatusOrder < 3 || auditStatusOrder >= 9)) ||
                                        (!isAudit && (jobStatusOrder < 3 || jobStatusOrder >= 11))
                                        ? 'opacity-70 cursor-not-allowed' : ''
                                    }`}
                                    onClick={handleGenerateCrossQuestions}
                                    disabled={
                                        isLoading || isCrossPolling || 
                                        (isAudit && (auditStatusOrder < 3 || auditStatusOrder >= 9)) ||
                                        (!isAudit && (jobStatusOrder < 3 || jobStatusOrder >= 11))
                                    }
                                >
                                    {(isLoading || isCrossPolling || 
                                      (isAudit && currentCandidate?.status === "Generating Cross Questions") ||
                                      (!isAudit && currentCandidate?.status === "Generating Report")) ? (
                                        <Loader2 className="animate-spin w-4 h-4" />
                                    ) : (
                                        isAudit ? <FileText className="w-4 h-4" /> : <Upload className="w-4 h-4" />
                                    )}
                                    {labels.view_r_btn2_gn}
                                </button>
                                <button
                                    className={`flex items-center gap-2 border border-gray-300 rounded-lg px-4 py-2 font-semibold text-gray-700 hover:bg-gray-100 transition w-full ${
                                        isLoading || isCrossPolling || 
                                        (isAudit && auditStatusOrder < 7) ||
                                        (!isAudit && (jobStatusOrder < 6 || jobStatusOrder >= 11))
                                        ? 'opacity-70 cursor-not-allowed' : ''
                                    }`}
                                    onClick={handleDownloadCrossQuestions}
                                    disabled={
                                        isLoading || isCrossPolling || 
                                        (isAudit && auditStatusOrder < 7) ||
                                        (!isAudit && (jobStatusOrder < 6 || jobStatusOrder >= 11))
                                    }
                                >
                                    {isLoading || isCrossPolling || 
                                     (isAudit && currentCandidate?.status === "Generating Cross Questions") ||
                                     (!isAudit && currentCandidate?.status === "Comparing Reports") ? (
                                        <Loader2 className="animate-spin w-4 h-4" />
                                    ) : (
                                        <Download className="w-4 h-4" />
                                    )}
                                    {labels.view_r_btn2_dl}
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Message/Loader */}
            {message && (
                <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg z-50 mb-2">
                    {message}
                </div>
            )}
            {/* {(isLoading || isPolling || isCrossPolling) && (
                <div className="fixed inset-0 flex items-center justify-center bg-white/60 z-40">
                    <Loader2 className="animate-spin w-10 h-10 text-blue-600" />
                </div>
            )} */}

            {/* Transcript Manager Modal */}
            <TranscriptManager
                isOpen={showTranscriptManager}
                onClose={() => setShowTranscriptManager(false)}
                onTranscriptFetched={handleTranscriptFetched}
                mainId={mainId}
                subId={subId}
                isAudit={isAudit}
            />
        </div>
    );
}

export default J_Candidates_Screening;