/* eslint-disable react/prop-types */
/* eslint-disable no-unused-vars */
import axios from 'axios';
import { ChevronDown, Download, FileText, Loader2, X } from 'lucide-react';
import { useEffect, useState } from 'react';

const API_BASE_URL_TRANSCRIPTS = '/transcripts'; // Use proxy instead of direct port 8001
const API_BASE_URL_AUD = 'http://localhost:8000/api/audit';
const API_BASE_URL_JOB = 'http://localhost:8000/api/jobs';

const TranscriptManager = ({ 
    isOpen, 
    onClose, 
    onTranscriptFetched, 
    mainId, 
    subId,
    isAudit 
}) => {
    const [jobId, setJobId] = useState(mainId || '');
    const [candidateId, setCandidateId] = useState(subId || '');
    const [isLoading, setIsLoading] = useState(false);
    const [message, setMessage] = useState('');
    const [transcript, setTranscript] = useState('');
    const [reportTemplates, setReportTemplates] = useState([]);
    const [selectedTemplate, setSelectedTemplate] = useState('');

    // Fetch report templates when component mounts
    useEffect(() => {
        const fetchReportTemplates = async () => {
            try {
                const response = await fetch('/api/policies/report_templates');
                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        setReportTemplates(data.data);
                        // Auto-select the first template if available
                        if (data.data.length > 0) {
                            setSelectedTemplate(data.data[0].id);
                        }
                    }
                }
            } catch (error) {
                console.error('Error fetching report templates:', error);
            }
        };

        fetchReportTemplates();
    }, []);

    const handleFetchTranscript = async () => {
        if (!jobId || !candidateId) {
            setMessage('Please enter both Job ID and Candidate ID');
            return;
        }

        setIsLoading(true);
        setMessage('');

        try {
            // Step 1: Get transcript list for specific job and candidate
            console.log(`Fetching transcript list from: ${API_BASE_URL_TRANSCRIPTS}/job/${jobId}/candidate/${candidateId}`);
            const listResponse = await axios.get(`${API_BASE_URL_TRANSCRIPTS}/job/${jobId}/candidate/${candidateId}`);
            
            console.log('List Response:', listResponse.data);
            
            if (listResponse.data && listResponse.data.total_count > 0) {
                // Step 2: Get the filename from the first transcript
                const filename = listResponse.data.transcripts[0].filename;
                setMessage(`Found transcript: ${filename}. Downloading full content...`);
                
                try {
                    // Step 3: Download the complete transcript
                    console.log(`Downloading transcript from: ${API_BASE_URL_TRANSCRIPTS}/${filename}/download`);
                    const fullResponse = await axios.get(`${API_BASE_URL_TRANSCRIPTS}/${filename}/download`);
                    
                    console.log('Full Response:', fullResponse.data);
                    
                    if (fullResponse.data) {
                        // Process the transcript data to extract conversation
                        const transcriptData = fullResponse.data;
                        let conversationText = '';
                        
                        // Add header information
                        conversationText += `Interview Transcript\n`;
                        conversationText += `Interview ID: ${transcriptData.interview_id}\n`;
                        conversationText += `Job ID: ${transcriptData.job_id}\n`;
                        conversationText += `Candidate ID: ${transcriptData.candidate_id}\n`;
                        conversationText += `Duration: ${transcriptData.duration_total} seconds\n`;
                        conversationText += `Start Time: ${transcriptData.start_time}\n`;
                        conversationText += `End Time: ${transcriptData.end_time}\n`;
                        conversationText += `\n--- CONVERSATION ---\n\n`;
                        
                        // Extract conversation entries
                        if (transcriptData.entries && transcriptData.entries.length > 0) {
                            transcriptData.entries.forEach(entry => {
                                if (entry.message_type === 'speech') {
                                    conversationText += `[${entry.timestamp}] ${entry.speaker}: ${entry.message}\n\n`;
                                }
                            });
                        } else {
                            conversationText += 'No conversation data available.\n';
                        }
                        
                        setTranscript(conversationText);
                        setMessage('Transcript fetched successfully! Click "Submit for Report" to proceed.');
                    } else {
                        setMessage('No transcript content received from download endpoint');
                    }
                } catch (downloadError) {
                    console.error('Download endpoint failed:', downloadError);
                    // Fallback: Use the summary data from the list response
                    setMessage('Download endpoint not available. Using transcript summary data...');
                    
                    const transcriptSummary = listResponse.data.transcripts[0];
                    let fallbackText = '';
                    
                    fallbackText += `Interview Transcript (Summary)\n`;
                    fallbackText += `Interview ID: ${transcriptSummary.interview_id}\n`;
                    fallbackText += `Meeting ID: ${transcriptSummary.meeting_id}\n`;
                    fallbackText += `Duration: ${transcriptSummary.duration_total} seconds\n`;
                    fallbackText += `Start Time: ${transcriptSummary.start_time}\n`;
                    fallbackText += `End Time: ${transcriptSummary.end_time}\n`;
                    fallbackText += `Participants: ${transcriptSummary.participants.join(', ')}\n`;
                    fallbackText += `Message Count: ${transcriptSummary.message_count}\n`;
                    fallbackText += `\n--- NOTE ---\n`;
                    fallbackText += `Full conversation details not available due to server configuration.\n`;
                    fallbackText += `Please check the transcript server's download endpoint.\n`;
                    
                    setTranscript(fallbackText);
                    setMessage('Transcript summary loaded. Full conversation details may require server configuration.');
                }
            } else {
                console.log('No transcript found. Response:', listResponse.data);
                setMessage(`No transcript found for Job ID: ${jobId}, Candidate ID: ${candidateId}`);
            }
        } catch (error) {
            console.error('Error fetching transcript:', error);
            if (error.response) {
                const status = error.response.status;
                if (status === 404) {
                    setMessage(`No transcript found for Job ID: ${jobId}, Candidate ID: ${candidateId}`);
                } else {
                    setMessage(error.response.data?.detail || `Error fetching transcript (${status})`);
                }
            } else {
                setMessage('Error connecting to transcript service. Make sure the transcript server is running on port 8001.');
            }
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmitForReport = async () => {
        if (!transcript) {
            setMessage('No transcript to submit');
            return;
        }

        if (!selectedTemplate) {
            setMessage('Please select a report template');
            return;
        }

        setIsLoading(true);
        setMessage('Submitting transcript for report generation...');

        try {
            // Create a blob from the transcript content
            const blob = new Blob([transcript], { type: 'text/plain' });
            
            // Create FormData and append the blob as a file
            const formData = new FormData();
            formData.append('transcript_file', blob, `transcript_job${jobId}_candidate${candidateId}.txt`);

            // Submit to the transcript endpoint with template_id parameter
            const response = await fetch(`/api/jobs/transcript/${jobId}/${candidateId}?template_id=${selectedTemplate}`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            const result = await response.json();
            setMessage('Report generation started successfully! The candidate status will be updated.');
            
            // Call the parent callback to start polling
            onTranscriptFetched();
            
            // Close the modal after a short delay
            setTimeout(() => {
                onClose();
            }, 2000);

        } catch (error) {
            console.error('Error submitting transcript:', error);
            setMessage(`Error submitting transcript: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };    const handleDownloadTranscript = () => {
        if (!transcript) {
            setMessage('No transcript to download');
            return;
        }

        const blob = new Blob([transcript], { type: 'text/plain' });
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `transcript_job${jobId}_candidate${candidateId}.txt`);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
        window.URL.revokeObjectURL(url);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-lg max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b">
                    <h2 className="text-xl font-semibold text-gray-900">
                        {isAudit ? 'Fetch Lab Transcript' : 'Fetch Interview Transcript'}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                    >
                        <X className="w-5 h-5 text-gray-500" />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {/* Input Section */}
                    <div className="grid grid-cols-2 gap-4 mb-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Job ID
                            </label>
                            <input
                                type="number"
                                value={jobId}
                                onChange={(e) => setJobId(e.target.value)}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="Enter job ID"
                                disabled={isLoading}
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Candidate ID
                            </label>
                            <input
                                type="number"
                                value={candidateId}
                                onChange={(e) => setCandidateId(e.target.value)}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                                placeholder="Enter candidate ID"
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    {/* Fetch Button */}
                    <button
                        onClick={handleFetchTranscript}
                        disabled={isLoading || !jobId || !candidateId}
                        className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold px-4 py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed mb-4"
                    >
                        {isLoading ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <Download className="w-4 h-4" />
                        )}
                        Fetch Transcript
                    </button>

                    {/* Message */}
                    {message && (
                        <div className={`p-4 rounded-lg mb-4 ${
                            message.includes('Error') || message.includes('error')
                                ? 'bg-red-50 text-red-800'
                                : 'bg-green-50 text-green-800'
                        }`}>
                            {message}
                        </div>
                    )}

                    {/* Transcript Preview */}
                    {transcript && (
                        <div className="mb-6">
                            <div className="flex items-center justify-between mb-2">
                                <label className="block text-sm font-medium text-gray-700">
                                    Transcript Content
                                </label>
                                <button
                                    onClick={handleDownloadTranscript}
                                    className="text-sm text-blue-600 hover:text-blue-800 font-medium flex items-center gap-1"
                                >
                                    <Download className="w-3 h-3" />
                                    Download
                                </button>
                            </div>
                            <div className="border border-gray-300 rounded-lg p-4 bg-gray-50 max-h-60 overflow-y-auto">
                                <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                                    {transcript}
                                </pre>
                            </div>
                        </div>
                    )}

                    {/* Report Template Selection */}
                    {transcript && reportTemplates.length > 0 && (
                        <div className="mb-6">
                            <label className="block text-sm font-medium text-gray-700 mb-2">
                                Select Report Template
                            </label>
                            <div className="relative">
                                <select
                                    value={selectedTemplate}
                                    onChange={(e) => setSelectedTemplate(e.target.value)}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 pr-10 bg-white text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none"
                                >
                                    <option value="">Select a template...</option>
                                    {reportTemplates.map((template) => (
                                        <option key={template.id} value={template.id}>
                                            {template.name}
                                        </option>
                                    ))}
                                </select>
                                <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
                            </div>
                            <p className="mt-1 text-xs text-gray-500">
                                Choose the report template that matches the job position for structured evaluation.
                            </p>
                        </div>
                    )}

                    {/* Action Buttons */}
                    <div className="flex gap-3">
                        <button
                            onClick={onClose}
                            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 font-semibold text-gray-700 hover:bg-gray-50 transition"
                        >
                            Cancel
                        </button>
                        {transcript && (
                            <button
                                onClick={handleSubmitForReport}
                                disabled={isLoading}
                                className="flex-1 flex items-center justify-center gap-2 bg-green-600 hover:bg-green-700 text-white font-semibold px-4 py-2 rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {isLoading ? (
                                    <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                    <FileText className="w-4 h-4" />
                                )}
                                Submit for Report
                            </button>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default TranscriptManager;