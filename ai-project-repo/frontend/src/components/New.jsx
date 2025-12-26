/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Route, Routes, Link, useLocation, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Menu, X, ChevronLeft, ChevronRight, Download, Loader2, Plus, AlertCircle, Upload } from 'lucide-react';
import { useLabels } from '../context/LabelsContext.jsx';

const API_BASE_URL_AUD = 'http://localhost:8000/api/audit';
const API_BASE_URL_JOB = 'http://localhost:8000/api/jobs';

function J_Candidates_New() {
  const [labName, setLabName] = useState('');
  const [description, setDescription] = useState('');
  const [questions, setQuestions] = useState(['']);
  const [fullName, setFullName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [email, setEmail] = useState('');
  const [resume, setResume] = useState(null);
  const [jobId, setJobId] = useState('');
  const [aspects, setAspects] = useState([{ name: '', focusAreas: [''] }]);
  const location = useLocation();
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [nameError, setNameError] = useState('');
  const [emailError, setEmailError] = useState('');
  const navigate = useNavigate();
  const { labels, switchLabels } = useLabels();
  const [isAudit, setIsAudit] = useState(location.pathname.startsWith('/audit'));

  useEffect(() => {
    // Extract job ID from URL query parameters
    const queryParams = new URLSearchParams(location.search);
    setIsAudit(location.pathname.startsWith('/audit'));

    const subId = isAudit
      ? queryParams.get('domainId')
      : queryParams.get('jobId');

    if (subId) {
      setJobId(subId);
    }
  }, [location.pathname, location.search]);

  const validateEmail = (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleLabNameChange = (e) => {
    const newName = e.target.value;
    setLabName(newName);

    // Clear error when user starts typing again
    if (nameError) {
      setNameError('');
    }
  };

  const addQuestion = () => {
    setQuestions([...questions, '']);
  };

  const handleQuestionChange = (index, value) => {
    const updatedQuestions = [...questions];
    updatedQuestions[index] = value;
    setQuestions(updatedQuestions);
  };

  const removeQuestion = (index) => {
    if (questions.length === 1) {
      // Don't remove the last question, just clear it
      const updatedQuestions = [...questions];
      updatedQuestions[0] = '';
      setQuestions(updatedQuestions);
    } else {
      const updatedQuestions = [...questions];
      updatedQuestions.splice(index, 1);
      setQuestions(updatedQuestions);
    }
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

    if (isAudit) {
      if (!labName.trim()) {
      setError('Lab name cannot be empty');
      setIsLoading(false);
      return;
    }

    try {
      const queryParams = new URLSearchParams(location.search);

      const filteredQuestions = questions.filter(q => q.trim() !== '');
      console.log('Filtered Questions:', filteredQuestions); // For debugging
      
      const response = await axios.post(`${API_BASE_URL_AUD}/labs`, { 
        name: labName, 
        description: description, 
        metadata: filteredQuestions,
        domain_id: queryParams.get('domainId')
      });
      
      console.log('Response:', response.data); // For debugging
      navigate(-1);
      setMessage('Lab Created successfully!');
    } catch (error) {
      console.error('Error details:', error.response || error); // For debugging
      
      // Handle specific error for duplicate lab name
      if (error.response?.status === 400 && error.response?.data?.detail?.includes('already exists')) {
        setNameError(error.response.data.detail);
        setError(error.response.data.detail);
      } else {
        setError(
          error.response?.data?.detail || 
          error.response?.data?.message || 
          error.message || 
          'Error creating lab'
        );
      }
    } finally {
      setIsLoading(false);
    }
    } else {
      // Validation
      if (!fullName.trim()) {
        setError('Full name is required');
        setIsLoading(false);
        return;
      }

      if (!email.trim()) {
        setError('Email is required');
        setIsLoading(false);
        return;
      }

      if (!validateEmail(email)) {
        setEmailError('Please enter a valid email address');
        setError('Please enter a valid email address');
        setIsLoading(false);
        return;
      }

      if (!resume) {
        setError('Resume is required');
        setIsLoading(false);
        return;
      }

      if (!jobId) {
        setError('Job ID is missing');
        setIsLoading(false);
        return;
      }

      try {
        // Create FormData for file upload
        const formData = new FormData();
        formData.append('full_name', fullName);
        formData.append('phone_number', phoneNumber);
        formData.append('email', email);
        formData.append('resume', resume);

        // Filter and format aspects
        const filteredAspects = aspects
          .filter(aspect => aspect.name && aspect.name.trim() !== '')
          .map(aspect => ({
            name: aspect.name,
            focusAreas: aspect.focusAreas ? aspect.focusAreas.filter(fa => fa.trim() !== '') : []
          }));

        formData.append('aspects', JSON.stringify(filteredAspects));

        // Note: job_id is now in the URL path, not form data

        const response = await axios.post(`${API_BASE_URL_JOB}/candidates/${jobId}`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });

        setMessage('Candidate added successfully!');
        navigate(-1);

        // Reset form
        setFullName('');
        setPhoneNumber('');
        setEmail('');
        setResume(null);
        setAspects([{ name: '', focusAreas: [''] }]);

        // Reset file input
        const fileInput = document.getElementById('resume-upload');
        if (fileInput) {
          fileInput.value = '';
        }

      } catch (error) {
        console.error('Error details:', error.response || error);

        setError(
          error.response?.data?.detail ||
          error.response?.data?.message ||
          error.message ||
          'Error adding candidate'
        );
      } finally {
        setIsLoading(false);
      }
    }
  };

  return (
    <div className="p-8 flex flex-col items-center">
      <h2 className="text-2xl mb-6 font-bold">Add New {labels.new_title}</h2>

      {isAudit ? (
        <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl w-full">
          <div>
            <label className="block mb-2 font-medium">Lab Name:</label>
            <div className="relative">
              <input
                type="text"
                value={labName}
                onChange={handleLabNameChange}
                className={`border p-2 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${nameError ? 'border-red-500' : ''
                  }`}
                disabled={isLoading}
              />
              {nameError && (
                <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                  <AlertCircle className="h-5 w-5 text-red-500" />
                </div>
              )}
            </div>
            {nameError && <p className="mt-1 text-sm text-red-600">{nameError}</p>}
          </div>
          <div>
            <label className="block mb-2 font-medium">Description:</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="border p-2 w-full h-32 rounded-lg shadow-sm"
              disabled={isLoading}
            />
          </div>

          {/* Info Section */}
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <label className="block font-medium">Relevant Information:</label>
              <button
                type="button"
                onClick={addQuestion}
                className="text-blue-600 hover:text-blue-800 flex items-center text-sm"
                disabled={isLoading}
              >
                <Plus className="h-4 w-4 mr-1" /> Add Info
              </button>
            </div>

            {questions.map((question, index) => (
              <div key={index} className="flex items-center gap-2">
                <input
                  type="text"
                  value={question}
                  onChange={(e) => handleQuestionChange(index, e.target.value)}
                  placeholder={`Information ${index + 1}`}
                  className="border p-2 flex-1 rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => removeQuestion(index)}
                  className="text-red-500 hover:text-red-700 p-2 rounded-full hover:bg-gray-100"
                  disabled={isLoading}
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            ))}
          </div>


          {/* Buttons */}
          <div className="flex flex-col gap-3 w-full">
            <button
              type="submit"
              className="bg-black hover:bg-gray-900 text-white px-6 py-2 rounded-lg transition-colors flex items-center justify-center w-full"
              disabled={isLoading || nameError || emailError}
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span className="ml-2">Adding...</span>
                </>
              ) : (
                <span>Add Lab</span>
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
      ) : (
        <form onSubmit={handleSubmit} className="space-y-4 max-w-2xl w-full">
          {/* Full Name */}
          <div>
            <label className="block mb-2 font-medium">Full Name: <span className="text-red-500">*</span></label>
            <div className="relative">
              <input
                type="text"
                value={fullName}
                onChange={handleFullNameChange}
                className={`border p-2 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${nameError ? 'border-red-500' : ''
                  }`}
                disabled={isLoading}
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
                className={`border p-2 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${emailError ? 'border-red-500' : ''
                  }`}
                disabled={isLoading}
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
                  {resume ? resume.name : 'Click to upload resume (PDF, DOC, DOCX)'}
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
              disabled={isLoading || nameError || emailError}
            >
              {isLoading ? (
                <>
                  <Loader2 className="animate-spin" size={20} />
                  <span className="ml-2">Adding...</span>
                </>
              ) : (
                <span>Add Candidate</span>
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
      )}



      {error && !nameError && !emailError && <p className="mt-4 text-red-600">{error}</p>}
      {message && <p className="mt-4 text-green-600">{message}</p>}
    </div>
  );
}

export default J_Candidates_New;