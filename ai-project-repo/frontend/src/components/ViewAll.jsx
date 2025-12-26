/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Menu, X, ChevronLeft, ChevronRight, Download, Loader2, RefreshCw, User, FileText, Calendar, Trash2 } from 'lucide-react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card';
import { useLabels } from '../context/LabelsContext';

const API_BASE_URL_AUD = 'http://localhost:8000/api/audit';
const API_BASE_URL_JOB = 'http://localhost:8000/api/jobs';

function J_Candidates() {
    const { labels, switchLabels } = useLabels();
    const [candidates, setCandidates] = useState([]);
    const [selectedCandidates, setSelectedCandidates] = useState([]); // New state for selected candidates
    const [selectedLab, setSelectedLab] = useState('');
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [currentJob, setCurrentJob] = useState(null);
    const navigate = useNavigate();
    const location = useLocation();
    const [isAudit, setIsAudit] = useState(location.pathname.startsWith('/audit'));

    useEffect(() => {
        const queryParams = new URLSearchParams(location.search);
        setIsAudit(location.pathname.startsWith('/audit'));
        
        const mainId = isAudit
            ? queryParams.get('domainId')
            : queryParams.get('jobId');
        if (mainId) {
            fetchJobDetails(mainId);
            fetchCandidates(mainId);
            switchLabels(isAudit
            ? 'audit'
            : 'job')
        } else {
            if (isAudit) {
                navigate(`/audit/`);
            } else {
                navigate(`/jobs/`);
            }
        }
    }, [location.pathname, location.search, navigate, labels]);

    const fetchJobDetails = async (mainId) => {
        try {
            const API_URL = isAudit
                ? `${API_BASE_URL_AUD}/domains/${mainId}`
                : `${API_BASE_URL_JOB}/descriptions/${mainId}`;
            const response = await axios.get(API_URL);
            if (response.data == null) {
                if (isAudit) {
                    navigate(`/audit/`);
                } else {
                    navigate(`/jobs/`);
                }
            } else {
                setCurrentJob(response.data);
            }
        } catch (error) {
            console.error(`Error fetching ${labels.dashboard_empty_first} details:`, error);
            setCurrentJob(null);
        }
    };

    const fetchCandidates = async (mainId = null) => {
        setIsLoading(true);
        try {
            const API_URL = isAudit
                ? `${API_BASE_URL_AUD}/labs?domainId=${mainId}`
                : `${API_BASE_URL_JOB}/candidates/${mainId}`;
            const response = await axios.get(API_URL);
            setCandidates(Array.isArray(response.data) ? response.data : []);
            setIsLoading(false);
        } catch (error) {
            console.error(`Error fetching ${labels.list_err}:`, error);
            setCandidates([]);
            setIsLoading(false);
        }
    };

    const handleRefresh = async () => {
        setIsRefreshing(true);
        const queryParams = new URLSearchParams(location.search);
        const mainId = isAudit
            ? queryParams.get('domainId')
            : queryParams.get('jobId');
        await fetchCandidates(mainId);
        setIsRefreshing(false);
    };

    const handleLabClick = (subId) => {
        const queryParams = new URLSearchParams(location.search);

        const mainId = isAudit
            ? queryParams.get('domainId')
            : queryParams.get('jobId');

        if (isAudit) {
            navigate(`/audit/labs/manage?domainId=${mainId}&labId=${subId}`);
        } else {
            navigate(`/jobs/candidates/screening?jobId=${mainId}&candidateId=${subId}`);
        }
    };

    const handleSelectAll = (e) => {
        if (e.target.checked) {
            const allCandidateIds = candidates.map(c => c.id);
            setSelectedCandidates(allCandidateIds);
        } else {
            setSelectedCandidates([]);
        }
    };

    const handleSelectOne = (e, candidateId) => {
        if (e.target.checked) {
            setSelectedCandidates(prev => [...prev, candidateId]);
        } else {
            setSelectedCandidates(prev => prev.filter(id => id !== candidateId));
        }
    };

    const handleDelete = async () => {
        const queryParams = new URLSearchParams(location.search);
        const mainId = isAudit
            ? queryParams.get('domainId')
            : queryParams.get('jobId');

        try {
            if (isAudit) {
                for (const subId of selectedCandidates) {
                    await axios.delete(`${API_BASE_URL_AUD}/labs/${mainId}/${subId}`);
                }
            } else {
                for (const subId of selectedCandidates) {
                    await axios.delete(`${API_BASE_URL_JOB}/candidates/${mainId}/${subId}`);
                }
            }

            // Refresh Candidates List + Clear Selection
            await fetchCandidates(mainId);
            setSelectedCandidates([]);
        } catch (error) {
            console.error(`Error deleting ${labels.list_err}:`, error);
        }
    };

    const handleBackToJobs = () => {
        if (isAudit) {
            navigate(`/audit/`);
        } else {
            navigate(`/jobs/`);
        }
    };

    return (
        <div className="min-h-screen bg-white flex flex-col items-center justify-start py-10 px-2">
            <Card className="w-full max-w-6xl mx-auto flex-1 flex flex-col">
                <CardHeader className="flex flex-row items-center justify-between mb-6">
                    <div className="flex items-center">
                        {currentJob && (
                            <>
                                <button
                                    onClick={handleBackToJobs}
                                    className="mr-2 p-1 rounded-full hover:bg-gray-100 transition-colors"
                                    title="Back to job descriptions"
                                >
                                    <ChevronLeft className="h-5 w-5 text-gray-600" />
                                </button>
                                <CardTitle className="text-4xl font-bold text-gray-900">
                                    {currentJob.name} - {labels.list_title}
                                </CardTitle>
                            </>
                        )}
                        {!currentJob && <CardTitle className="text-4xl font-bold text-gray-900">{labels.list_title}</CardTitle>}
                    </div>
                    <div className="flex items-center space-x-2">
                        {selectedCandidates.length > 0 && (
                            <button
                                onClick={handleDelete}
                                className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                                title="Delete selected candidates"
                            >
                                <Trash2 className="h-5 w-5 text-red-600" />
                            </button>
                        )}
                        <button
                            onClick={handleRefresh}
                            className="p-2 rounded-full hover:bg-gray-100 transition-colors"
                            disabled={isRefreshing}
                            title="Refresh candidates"
                        >
                            <RefreshCw className={`h-5 w-5 text-gray-600 ${isRefreshing ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </CardHeader>
                <CardContent className="flex-1 overflow-auto">
                    <div className="overflow-auto max-h-[calc(100vh-250px)]">
                        <Table>
                            <TableHeader className="sticky top-0 bg-white">
                                <TableRow>
                                    <TableHead>
                                        <input
                                            type="checkbox"
                                            onChange={handleSelectAll}
                                            checked={selectedCandidates.length === candidates.length && candidates.length > 0}
                                        />
                                    </TableHead>
                                    <TableHead>{labels.list_col1}</TableHead>
                                    <TableHead>{labels.list_col2}</TableHead>
                                    <TableHead>Status</TableHead>
                                    <TableHead>Score</TableHead>
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {isLoading ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center py-8">
                                            <div className="flex justify-center items-center">
                                                <Loader2 className="h-6 w-6 animate-spin mr-2" />
                                                <span>Loading {labels.list_err}...</span>
                                            </div>
                                        </TableCell>
                                    </TableRow>
                                ) : candidates.length === 0 ? (
                                    <TableRow>
                                        <TableCell colSpan={5} className="text-center text-gray-500 py-8">
                                            No {labels.list_err} found
                                        </TableCell>
                                    </TableRow>
                                ) : (
                                    candidates.map((candidate, index) => (
                                        <TableRow
                                            key={candidate.id}
                                            onClick={() => handleLabClick(candidate.id)}
                                            className={`cursor-pointer hover:bg-gray-100 transition-colors ${candidate.status && candidate.status.toLowerCase().startsWith('generating') ? 'bg-yellow-50' : ''}`}
                                        >
                                            <TableCell>
                                                <input
                                                    type="checkbox"
                                                    checked={selectedCandidates.includes(candidate.id)}
                                                    onChange={(e) => handleSelectOne(e, candidate.id)}
                                                    onClick={(e) => e.stopPropagation()}
                                                />
                                            </TableCell>
                                            <TableCell>{candidate.id}</TableCell>
                                            <TableCell>{isAudit ? candidate.name : candidate.full_name }</TableCell>
                                            
                                            <TableCell>
                                                {candidate.status ? (
                                                    <span className="inline-block px-3 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-700">
                                                        {candidate.status}
                                                    </span>
                                                ) : 'N/A'}
                                            </TableCell>
                                            <TableCell>
                                                {candidate.score === null || candidate.score === undefined ? "N/A" : candidate.score}
                                            </TableCell>
                                        </TableRow>
                                    ))
                                )}
                            </TableBody>
                        </Table>
                    </div>
                </CardContent>
            </Card>
            <div className="pt-10 w-full max-w-6xl flex justify-center">
                <button
                    type='button'
                    className='bg-black hover:bg-gray-900 text-white px-6 py-2 rounded-lg transition-colors flex items-center space-x-2'
                    onClick={() => {
                        const queryParams = new URLSearchParams(location.search);
                        if (isAudit) {
                            navigate(`/audit/labs/new?domainId=${queryParams.get('domainId')}`);
                        } else {
                            navigate(`/jobs/candidates/new?jobId=${queryParams.get('jobId')}`);
                        }
                    }}
                >
                    <span>{labels.list_btn}</span>
                </button>
            </div>
        </div>
    );
}

export default J_Candidates;