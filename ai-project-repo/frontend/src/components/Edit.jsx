/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Menu, X, ChevronLeft, ChevronRight, Download, Loader2, Plus, AlertCircle, Upload } from 'lucide-react';
import { useLabels } from '../context/LabelsContext.jsx';

const API_BASE_URL_JOB = 'http://localhost:8000/api/jobs';

function J_Candidates_Edit() {
  const [jobId, setJobId] = useState('');
  const [candidateId, setCandidateId] = useState('');

  const [currentCandidate, setCurrentCandidate] = useState(null);
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [resume, setResume] = useState(null);
  const [aspects, setAspects] = useState([{ name: '', focusAreas: [''] }]);
  const location = useLocation();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [nameError, setNameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const navigate = useNavigate();
  const { labels, switchLabels } = useLabels();

  useEffect(() => {
    const queryParams = new URLSearchParams(location.search);
    
    const jobIdParam = queryParams.get('jobId');
    if (jobIdParam) {
      setJobId(jobIdParam);
    } else {
      navigate('/jobs');
    }

    const candidateIdParam = queryParams.get('candidateId');
    if (candidateIdParam) {
      setCandidateId(candidateIdParam);
    } else {
      navigate(`/jobs/candidates?jobId=${jobIdParam}`);
    };

    fetchCandidateDetails(jobIdParam, candidateIdParam);
  }, [location.pathname, location.search]);

  const fetchCandidateDetails = async (mId, sId) => {
    setIsLoading(true);

    try {
      const API_URL = `${API_BASE_URL_JOB}/candidates/${mId}/${sId}`;
      const response = await axios.get(API_URL);

      if (response.data == null) {
        navigate(`/jobs/candidates?jobId=${mId}`);
      } else {
        setCurrentCandidate(response.data);
      }
    } catch (error) {
      console.error('Error fetching candidate details:', error);
      setMessage('Error loading candidate details');
    } finally {
      setIsLoading(false);
    }
  };


  useEffect(() => {
    if (currentCandidate) {
      console.log(currentCandidate)
      setFullName(currentCandidate.full_name || '');
      setEmail(currentCandidate.email || '');
      setPhoneNumber(currentCandidate.phone_number || '');
      
      // Pre-fill aspects and focus areas
      if (Array.isArray(currentCandidate.aspects) && currentCandidate.aspects.length > 0) {
        setAspects(
          currentCandidate.aspects.map(a => ({
            name: a.name || '',
            focusAreas: Array.isArray(a.focusAreas) && a.focusAreas.length > 0
              ? a.focusAreas
              : ['']
          }))
        );
      } else {
        setAspects([{ name: '', focusAreas: [''] }]);
      }
    }
  }, [currentCandidate]);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleFullNameChange = (e) => {
    const newName = e.target.value;
    setFullName(newName);

    // Clear error when user starts typing again
    if (nameError) {
      setNameError('');
    }
  };

  const handleEmailChange = (e) => {
    const newEmail = e.target.value;
    setEmail(newEmail);

    // Clear error when user starts typing again
    if (emailError) {
      setEmailError('');
    }
  };

  const handleEmailBlur = () => {
    if (email && !validateEmail(email)) {
      setEmailError('Please enter a valid email address');
    }
  };

  const handleResumeChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      // Check file type (allow PDF, DOC, DOCX)
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      if (!allowedTypes.includes(file.type)) {
        setError('Please upload a PDF, DOC, or DOCX file');
        return;
      }

      // Check file size (limit to 5MB)
      if (file.size > 5 * 1024 * 1024) {
        setError('File size must be less than 5MB');
        return;
      }

      setResume(file);
      setError(''); // Clear any previous errors
    }
  };

  const handleAspectNameChange = (index, value) => {
    const updatedAspects = [...aspects];
    updatedAspects[index].name = value;
    setAspects(updatedAspects);
  };

  const handleFocusAreaChange = (aspectIndex, focusAreaIndex, value) => {
    const updatedAspects = [...aspects];
    updatedAspects[aspectIndex].focusAreas[focusAreaIndex] = value;
    setAspects(updatedAspects);
  };

  const addAspect = () => {
    setAspects([...aspects, { name: '', focusAreas: [''] }]);
  };

  const removeAspect = (index) => {
    if (aspects.length === 1) {
      // Don't remove the last aspect, just clear it
      setAspects([{ name: '', focusAreas: [''] }]);
    } else {
      const updatedAspects = [...aspects];
      updatedAspects.splice(index, 1);
      setAspects(updatedAspects);
    }
  };

  const addFocusArea = (aspectIndex) => {
    const updatedAspects = [...aspects];
    updatedAspects[aspectIndex].focusAreas.push('');
    setAspects(updatedAspects);
  };

  const removeFocusArea = (aspectIndex, focusAreaIndex) => {
    const updatedAspects = [...aspects];
    if (updatedAspects[aspectIndex].focusAreas.length === 1) {
      // Don't remove the last focus area, just clear it
      updatedAspects[aspectIndex].focusAreas[0] = '';
    } else {
      updatedAspects[aspectIndex].focusAreas.splice(focusAreaIndex, 1);
    }
    setAspects(updatedAspects);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage('');
    setError('');
    setIsLoading(true);

    // Validation
    if (!jobId || !candidateId) {
      setError('Job ID or Candidate ID is missing');
      setIsLoading(false);
      return;
    }

    try {
      // Create FormData for file upload
      const formData = new FormData();

      // Only send resume if a new file was uploaded
      if (resume) {
        formData.append('resume', resume);
      }
      
      // Always send phone number and aspects
      formData.append('phone_number', phoneNumber);

      // Filter and format aspects
      const filteredAspects = aspects
        .filter(aspect => aspect.name && aspect.name.trim() !== '')
        .map(aspect => ({
          name: aspect.name,
          focusAreas: aspect.focusAreas ? aspect.focusAreas.filter(fa => fa.trim() !== '') : []
        }));

      formData.append('aspects', JSON.stringify(filteredAspects));

      // PUT request for update
      const response = await axios.put(
        `${API_BASE_URL_JOB}/candidates/${jobId}/${candidateId}`,
        formData,
        { headers: { 'Content-Type': 'multipart/form-data' } }
      );

      setMessage('Candidate updated successfully!');
      navigate(`/jobs/candidates/screening?jobId=${jobId}&candidateId=${candidateId}`);

    } catch (error) {
      console.error('Error details:', error.response || error);
      console.error('Full error response:', error.response?.data);

      let errorMsg = error.message || 'Error updating candidate';
      if (error.response?.data?.detail) {
        if (Array.isArray(error.response.data.detail)) {
          errorMsg = error.response.data.detail.map(e => e.msg || e).join(', ');
        } else if (typeof error.response.data.detail === 'string') {
          errorMsg = error.response.data.detail;
        }
      } else if (error.response?.data?.message) {
        errorMsg = error.response.data.message;
      }

      setError(errorMsg);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-8 flex flex-col items-center">
      <h2 className="text-2xl mb-6 font-bold">Edit {labels.new_title}</h2>

      <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl w-full">
        {/* Full Name */}
        <div>
          <label className="block mb-2 font-medium">Full Name: <span className="text-red-500">*</span></label>
          <div className="relative">
            <input
              type="text"
              value={fullName}
              onChange={handleFullNameChange}
              className={`input-fullname-disabled border p-2 w-full rounded-lg shadow-sm bg-gray-100 text-gray-500 cursor-not-allowed ${nameError ? 'border-red-500' : ''}`}
              disabled={true}
              required
            />
            {nameError && (
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <AlertCircle className="h-5 w-5 text-red-500" />
              </div>
            )}
          </div>
          {nameError && <p className="mt-1 text-sm text-red-600">{nameError}</p>}
        </div>

        {/* Phone Number */}
        <div>
          <label className="block mb-2 font-medium">Phone Number:</label>
          <input
            type="tel"
            value={phoneNumber}
            onChange={(e) => setPhoneNumber(e.target.value)}
            className="border p-2 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            disabled={isLoading}
            placeholder="e.g., +1234567890"
          />
        </div>

        {/* Email */}
        <div>
          <label className="block mb-2 font-medium">Email: <span className="text-red-500">*</span></label>
          <div className="relative">
            <input
              type="email"
              value={email}
              onChange={handleEmailChange}
              onBlur={handleEmailBlur}
              className={`input-email-disabled border p-2 w-full rounded-lg shadow-sm bg-gray-100 text-gray-500 cursor-not-allowed ${emailError ? 'border-red-500' : ''}`}
              disabled={true}
              required
            />
            {emailError && (
              <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                <AlertCircle className="h-5 w-5 text-red-500" />
              </div>
            )}
          </div>
          {emailError && <p className="mt-1 text-sm text-red-600">{emailError}</p>}
        </div>

        {/* Resume Upload */}
        <div>
          <label className="block mb-2 font-medium">Resume: <span className="text-red-500">*</span></label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-gray-400 transition-colors">
            <input
              id="resume-upload"
              type="file"
              onChange={handleResumeChange}
              accept=".pdf,.doc,.docx"
              className="hidden"
              disabled={isLoading}
            />
            <label htmlFor="resume-upload" className="cursor-pointer">
              <Upload className="h-8 w-8 mx-auto mb-2 text-gray-400" />
              <p className="text-sm text-gray-600">
                {resume
                  ? resume.name
                  : currentCandidate?.resume
                    ? (() => {
                        const parts = currentCandidate.resume.split(/[/\\]+/);
                        return parts[parts.length - 1];
                      })()
                    : 'Click to upload resume (PDF, DOC, DOCX)'
                }
              </p>
              <p className="text-xs text-gray-400 mt-1">Max size: 5MB</p>
            </label>
          </div>
        </div>

        {/* Skills/Aspects Section */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <label className="block font-medium">Skills & Specializations:</label>
            <button
              type="button"
              onClick={addAspect}
              className="text-blue-600 hover:text-blue-800 flex items-center text-sm"
              disabled={isLoading}
            >
              <Plus className="h-4 w-4 mr-1" /> Add Skill Category
            </button>
          </div>

          <p className="text-xs text-gray-500">
            Skill categories are major areas of expertise. Specific skills are detailed skills within each category.
          </p>

          <div className="space-y-4">
            {aspects.map((aspect, aspectIndex) => (
              <div key={aspectIndex} className="border p-3 rounded-md">
                <div className="flex items-center gap-2 mb-2">
                  <input
                    type="text"
                    value={aspect.name}
                    onChange={(e) => handleAspectNameChange(aspectIndex, e.target.value)}
                    placeholder="e.g., Programming Languages, Frameworks, Certifications"
                    className="border p-2 flex-1 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => removeAspect(aspectIndex)}
                    className="text-red-500 hover:text-red-700 p-2 rounded-full hover:bg-gray-100"
                    disabled={isLoading || aspects.length === 1}
                  >
                    <X className="h-4 w-4" />
                  </button>
                </div>

                {/* Focus Areas for this aspect */}
                <div className="pl-4 space-y-2">
                  <div className="flex items-center justify-between mb-2">
                    <label className="text-sm font-medium text-gray-700">Specific Skills:</label>
                    <button
                      type="button"
                      onClick={() => addFocusArea(aspectIndex)}
                      className="text-blue-600 hover:text-blue-800 flex items-center text-xs"
                      disabled={isLoading}
                    >
                      <Plus className="h-3 w-3 mr-1" /> Add Skill
                    </button>
                  </div>

                  {aspect.focusAreas.map((focusArea, focusAreaIndex) => (
                    <div key={focusAreaIndex} className="flex items-center gap-2">
                      <input
                        type="text"
                        value={focusArea}
                        onChange={(e) => handleFocusAreaChange(aspectIndex, focusAreaIndex, e.target.value)}
                        placeholder="e.g., Python, React, AWS Certification"
                        className="border p-1 flex-1 rounded shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                        disabled={isLoading}
                      />
                      <button
                        type="button"
                        onClick={() => removeFocusArea(aspectIndex, focusAreaIndex)}
                        disabled={aspect.focusAreas.length === 1}
                        className="text-red-500 hover:text-red-700 p-1 rounded-full hover:bg-gray-100"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex flex-col gap-3 w-full">
          <button
            type="submit"
            className="bg-black hover:bg-gray-900 text-white px-6 py-2 rounded-lg transition-colors flex items-center justify-center w-full"
            disabled={isLoading}
          >
            {isLoading ? (
              <>
                <Loader2 className="animate-spin" size={20} />
                <span className="ml-2">Updating...</span>
              </>
            ) : (
              <span>Update Candidate</span>
            )}
          </button>
          <button
            type="button"
            onClick={() => navigate(-1)}
            className="bg-white border border-black text-black hover:bg-gray-100 px-6 py-2 rounded-lg transition-colors w-full"
            disabled={isLoading}
          >
            Cancel
          </button>
        </div>
      </form>

      {error && <p className="mt-4 text-red-600">{error}</p>}
      {nameError && <p className="mt-2 text-red-600">{nameError}</p>}
      {emailError && <p className="mt-2 text-red-600">{emailError}</p>}
      {message && <p className="mt-4 text-green-600">{message}</p>}
    </div>
  );
}

export default J_Candidates_Edit;