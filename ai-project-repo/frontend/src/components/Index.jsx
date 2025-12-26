/* eslint-disable no-unused-vars */
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import axios from 'axios';
import { Edit, Trash2, Loader2, Plus, ChevronRight, X, Info } from 'lucide-react';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from '@/components/ui/alert-dialog';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { useLabels } from '../context/LabelsContext';

const API_BASE_URL_JOB = 'http://localhost:8000/api/jobs';
const API_BASE_URL_AUD = 'http://localhost:8000/api/audit';

// Guidance Content
const GUIDANCE = {
  job: {
    main: {
      name: {
        placeholder: "e.g., Junior Software Development Engineer",
        examples: ["Junior Software Development Engineer", "TO DO EXAMPLES"]
      },
      description: {
        placeholder: "Clearly outline responsibilities and how the role contributes to the company...",
        example: "TO DO EXAMPLE"
      }
    },
    aspect: {
      examples: ["Bachelor Degree", "Master Degree", "Certifications", "Skills", "Passions"]
    },
    focusArea: {
      examples: ["Computer Science", "IT", "LLM", "Python", "Teamwork", "Security"]
    },
  },
  domain: {
    main: {
      name: {
        placeholder: "e.g., Information Security, Financial Management, Customer Service",
        examples: ["Information Security", "Financial Management", "Human Resources", "Customer Service", "Supply Chain Management"]
      },
      description: {
        placeholder: "Describe what this domain covers and why it's important for your organization...",
        example: "This domain covers all aspects of protecting organizational data, systems, and networks from cyber threats. It includes policies, procedures, and technologies used to safeguard sensitive information and ensure business continuity."
      }
    },
    aspect: {
      examples: ["Access Control", "Data Protection", "Network Security", "Incident Response", "Risk Assessment"]
    },
    focusArea: {
      examples: ["User Authentication", "Password Policies", "Multi-factor Authentication", "Role-based Access", "Privileged Account Management"]
    }
  }
};

function J_Index() {
  const { labels, switchLabels } = useLabels();
  const [jobs, setJobs] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const DEFAULT_FORM_DATA = {
    name: '',
    description: '',
    aspects: [{ name: '', focusAreas: [''] }] // Initialize With One Empty Aspect & Focus Area
  };
  const [formData, setFormData] = useState(DEFAULT_FORM_DATA);
  const [editingJob, setEditingJob] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [error, setError] = useState(null);
  const [showGuidance, setShowGuidance] = useState(true);
  const [formError, setFormError] = useState("");
  const navigate = useNavigate();
  const location = useLocation();
  const [isAudit, setIsAudit] = useState(location.pathname.startsWith('/audit'));

  useEffect(() => {
    setIsAudit(location.pathname.startsWith('/audit'));
  }, [location.pathname]);

  useEffect(() => {
    fetchDescriptions();
  }, [isAudit]);

  const fetchDescriptions = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const API_URL = isAudit
        ? `${API_BASE_URL_AUD}/domains`
        : `${API_BASE_URL_JOB}/descriptions`;
      const response = await axios.get(API_URL);
      // Make Sure response.data Is Always An Array
      const descriptionsData = Array.isArray(response.data) ? response.data :
        (response.data && response.data.jobs && Array.isArray(response.data.jobs)) ?
          response.data.jobs : [];
      setJobs(descriptionsData);
    } catch (error) {
      console.error(`Error fetching ${labels.dashboard_empty}:`, error);
      setError(`Failed to load ${labels.dashboard_empty}. Please try again later.`);
      // Ensure description is an empty array on error
      setJobs([]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleAspectNameChange = (index, value) => {
    const updatedAspects = [...formData.aspects];
    updatedAspects[index].name = value;
    setFormData(prev => ({ ...prev, aspects: updatedAspects }));
  };

  const handleFocusAreaChange = (aspectIndex, focusAreaIndex, value) => {
    const updatedAspects = [...formData.aspects];
    updatedAspects[aspectIndex].focusAreas[focusAreaIndex] = value;
    setFormData(prev => ({ ...prev, aspects: updatedAspects }));
  };

  const addAspect = () => {
    setFormData(prev => ({
      ...prev,
      aspects: [...prev.aspects, { name: '', focusAreas: [''] }]
    }));
  };

  const removeAspect = (index) => {
    const updatedAspects = [...formData.aspects];
    updatedAspects.splice(index, 1);
    setFormData(prev => ({ ...prev, aspects: updatedAspects }));
  };

  const addFocusArea = (aspectIndex) => {
    const updatedAspects = [...formData.aspects];
    updatedAspects[aspectIndex].focusAreas.push('');
    setFormData(prev => ({ ...prev, aspects: updatedAspects }));
  };

  const removeFocusArea = (aspectIndex, focusAreaIndex) => {
    const updatedAspects = [...formData.aspects];
    updatedAspects[aspectIndex].focusAreas.splice(focusAreaIndex, 1);
    setFormData(prev => ({ ...prev, aspects: updatedAspects }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsSubmitting(true);
    setFormError(""); // Reset form error

    // Filter out any empty aspects or focus areas
    const dataToSubmit = {
      ...formData,
      aspects: formData.aspects
        .map(aspect => ({
          ...aspect,
          name: aspect.name.trim(),
          focusAreas: aspect.focusAreas.filter(fa => fa.trim() !== '')
        }))
        .filter(aspect => aspect.name !== '' && aspect.focusAreas.length > 0)
    };

    if (isAudit) {
      for (const aspect of formData.aspects) {
        if (aspect.name.trim() === '') {
          setFormError("Each aspect must have a name.");
          setIsSubmitting(false);
          return;
        }
        if (!aspect.focusAreas.length || aspect.focusAreas.every(fa => fa.trim() === '')) {
          setFormError("Each aspect must have at least one focus area.");
          setIsSubmitting(false);
          return;
        }
      }

      if (!formData.aspects.length || formData.aspects.every(aspect => aspect.name.trim() === '')) {
        setFormError("At least one aspect is required.");
        setIsSubmitting(false);
        return;
      }
    }

    try {
      if (editingJob) {
        // Update Existing Item
        const API_URL = isAudit
          ? `${API_BASE_URL_AUD}/domains/${editingJob.id}`
          : `${API_BASE_URL_JOB}/descriptions/${editingJob.id}`;
        await axios.put(API_URL, dataToSubmit);
      } else {
        // Create New Item
        const API_URL = isAudit
          ? `${API_BASE_URL_AUD}/domains`
          : `${API_BASE_URL_JOB}/descriptions`;
        await axios.post(API_URL, dataToSubmit);
      }

      // Reset form and refresh descriptions
      setFormData(DEFAULT_FORM_DATA);
      setEditingJob(null);
      setDialogOpen(false);
      fetchDescriptions();
    } catch (error) {
      console.error(`Error saving ${labels.dashboard_empty_first}:`, error);
      setError(`Error saving ${labels.dashboard_empty_first}. Please try again.`);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleEdit = (job) => {
    setEditingJob(job);

    // Initialize with existing aspects or a default structure
    const aspects = (job.aspects && Array.isArray(job.aspects) && job.aspects.length > 0)
      ? job.aspects.map(aspect => ({
        name: aspect.name || '',
        focusAreas: Array.isArray(aspect.focusAreas) && aspect.focusAreas.length > 0
          ? aspect.focusAreas
          : ['']
      }))
      : [{ name: '', focusAreas: [''] }];

    setFormData({
      name: job.name || '',
      description: job.description || '',
      aspects: aspects
    });

    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    try {
      const API_URL = isAudit
        ? `${API_BASE_URL_AUD}/domains/${id}`
        : `${API_BASE_URL_JOB}/descriptions/${id}`;

      await axios.delete(API_URL);
      fetchDescriptions();
    } catch (error) {
      console.error(`Error deleting ${labels.dashboard_word}:`, error);
      setError(`Error deleting ${labels.dashboard_word}. Please try again.`);
    }
  };

  const handleJobClick = (subId) => {
    if (isAudit) {
      navigate(`/audit/labs?domainId=${subId}`);
    } else {
      navigate(`/jobs/candidates?jobId=${subId}`);
    }
  };

  const openNewJobDialog = () => {
    setEditingJob(null);
    setFormData({ name: '', description: '', aspects: [{ name: '', focusAreas: [''] }] });
    setShowGuidance(true);
    setDialogOpen(true);
  };

  // Calculate total focus areas (for all aspects) of a job description
  const getTotalFocusAreas = (job) => {
    if (!job.aspects || !Array.isArray(job.aspects)) return 0;

    return job.aspects.reduce((total, aspect) => {
      if (!aspect.focusAreas || !Array.isArray(aspect.focusAreas)) return total;
      return total + aspect.focusAreas.length;
    }, 0);
  };

  // Component for guidance panel
  const GuidancePanel = () => (
    <div className={`bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4 ${showGuidance ? 'block' : 'hidden'}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center">
          <Info className="h-5 w-5 text-blue-600 mr-2" />
          <h3 className="font-medium text-blue-900">How to fill out this form</h3>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() => setShowGuidance(false)}
          className="text-blue-600"
        >
          <X className="h-4 w-4" />
        </Button>
      </div>

      <div className="space-y-3 text-sm text-blue-800">
        <div>
          <p className="font-medium">{labels.dashboard_new_t1}</p>
          <p>{labels.dashboard_new_l1} (e.g., {GUIDANCE[labels.dashboard_word].main.name.examples.slice(0, 3).join(', ')})</p>
        </div>

        <div>
          <p className="font-medium">{labels.dashboard_new_t2}</p>
          <p>{labels.dashboard_new_l2}</p>
        </div>

        <div>
          <p className="font-medium">{labels.dashboard_new_t3}</p>
          <p>{labels.dashboard_new_l3} (e.g., {GUIDANCE[labels.dashboard_word].aspect.examples.slice(0, 3).join(', ')})</p>
        </div>

        <div>
          <p className="font-medium">{labels.dashboard_new_t4}</p>
          <p>{labels.dashboard_new_l4} (e.g., {GUIDANCE[labels.dashboard_word].focusArea.examples.slice(0, 3).join(', ')})</p>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6 flex flex-col items-center space-y-6 min-h-screen">
      <h1 className="text-2xl font-bold">{labels.dashboard_title}</h1>

      <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* New Job Card */}
        <Card className="hover:shadow-md transition-shadow cursor-pointer flex flex-col h-60" onClick={openNewJobDialog}>
          <CardHeader className="flex-1 flex justify-center items-center">
            <CardTitle className="text-center flex flex-col items-center">
              <Plus className="h-12 w-12 text-gray-400 mb-2" />
              <span>{labels.dashboard_create_new}</span>
            </CardTitle>
          </CardHeader>
        </Card>

        {/* Error State */}
        {error && (
          <Card className="col-span-full flex justify-center items-center h-60 bg-red-50">
            <div className="text-center p-4">
              <p className="text-red-600 mb-3">{error}</p>
              <Button onClick={fetchDescriptions}>Retry</Button>
            </div>
          </Card>
        )}

        {/* Loading State */}
        {isLoading && (
          <Card className="flex justify-center items-center h-60">
            <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
          </Card>
        )}

        {/* Job Cards - Only render if not loading and jobs exists */}
        {!isLoading && !error && Array.isArray(jobs) && jobs.map((job) => (
          <Card key={job.id} className="hover:shadow-md transition-shadow cursor-pointer flex flex-col h-60">
            <div className="flex flex-col flex-1 h-full" onClick={() => handleJobClick(job.id)}>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <span>{job.name}</span>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-500 line-clamp-3">{job.description}</p>
                <div className="mt-2">
                  <p className="text-sm font-medium text-gray-700">
                    {job.aspects && Array.isArray(job.aspects) ? (
                      <>Aspects: {job.aspects.length} | Focus Areas: {getTotalFocusAreas(job)}</>
                    ) : (
                      <>No aspects defined</>
                    )}
                  </p>
                </div>
              </CardContent>
              <div className="flex-1" />
            </div>
            <CardFooter className="bg-gray-50 p-4 rounded-b-lg flex justify-between mt-auto">
              <Button
                variant="outline"
                size="sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleEdit(job);
                }}
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit
              </Button>

              <AlertDialog>
                <AlertDialogTrigger asChild>
                  <Button
                    variant="outline"
                    size="sm"
                    className="text-red-500 hover:text-red-700"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>{labels.dashboard_dlt_title}</AlertDialogTitle>
                    <AlertDialogDescription>
                      Are you sure you want to delete the {labels.dashboard_word} - {job.name}? This action cannot be undone.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                    <AlertDialogAction
                      className="bg-red-500 hover:bg-red-700"
                      onClick={() => handleDelete(job.id)}
                    >
                      Delete
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </CardFooter>
          </Card>
        ))}

        {/* Empty State - No jobs */}
        {!isLoading && !error && Array.isArray(jobs) && jobs.length === 0 && (
          <Card className="col-span-full flex justify-center items-center h-60 bg-gray-50">
            <div className="text-center p-4">
              <p className="text-gray-500 mb-3">No {labels.dashboard_empty} found. Create your first {labels.dashboard_empty_first} to get started.</p>
            </div>
          </Card>
        )}
      </div>

      {/* Dialog for Create/Edit Job Description */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingJob ? labels.dashboard_edit_title : labels.dashboard_new_title}</DialogTitle>
          </DialogHeader>

          {/* Guidance Panel */}
          {!editingJob && <GuidancePanel />}

          {!showGuidance && !editingJob && (
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => setShowGuidance(true)}
              className="text-blue-600 self-start mb-4"
            >
              <Info className="h-4 w-4 mr-1" />
              Show guidance
            </Button>
          )}

          {/* Show form validation error if present */}
          {formError && (
            <div className="mb-4 p-2 bg-red-100 text-red-700 rounded text-sm">
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit}>
            <div className="space-y-4">
              <div>
                <Label htmlFor="name">{labels.dashboard_form_title}<span className="text-red-500">*</span></Label>
                <Input
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder={GUIDANCE[labels.dashboard_word].main.name.placeholder}
                  required
                />
                <p className="text-xs text-gray-500 mt-1">
                  Examples: {GUIDANCE[labels.dashboard_word].main.name.examples.slice(0, 3).join(', ')}
                </p>
              </div>

              <div>
                <Label htmlFor="description">Description<span className="text-red-500">*</span></Label>
                <Textarea
                  id="description"
                  name="description"
                  value={formData.description}
                  onChange={handleInputChange}
                  placeholder={GUIDANCE[labels.dashboard_word].main.description.placeholder}
                  rows={4}
                  required
                />
                <details className="mt-1">
                  <summary className="text-xs text-blue-600 cursor-pointer hover:text-blue-800">
                    View example description
                  </summary>
                  <p className="text-xs text-gray-600 mt-1 p-2 bg-gray-50 rounded">
                    {GUIDANCE[labels.dashboard_word].main.description.example}
                  </p>
                </details>
              </div>

              {/* Aspects Section */}
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label>Aspects & Focus Areas{isAudit ? (<span className="text-red-500">*</span>) : (<></>)}</Label>
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={addAspect}
                    className="flex items-center text-blue-600"
                  >
                    <Plus className="h-4 w-4 mr-1" /> Add Aspect
                  </Button>
                </div>

                <p className="text-xs text-gray-500">
                  Aspects are major requirement categories. Focus areas are specific requirements or skills within each category.
                </p>

                <Accordion type="multiple" className="w-full">
                  {formData.aspects.map((aspect, aspectIndex) => (
                    <AccordionItem key={aspectIndex} value={`aspect-${aspectIndex}`} className="border p-3 rounded-md mb-2">
                      <div className="flex items-center gap-2 mb-2">
                        <Input
                          value={aspect.name}
                          onChange={(e) => handleAspectNameChange(aspectIndex, e.target.value)}
                          placeholder={`e.g., ${GUIDANCE[labels.dashboard_word].aspect.examples[aspectIndex % GUIDANCE[labels.dashboard_word].aspect.examples.length]}`}
                          className="flex-1"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="icon"
                          onClick={() => removeAspect(aspectIndex)}
                          disabled={formData.aspects.length === 1}
                          className="text-red-500 hover:text-red-700"
                        >
                          <X className="h-4 w-4" />
                        </Button>
                      </div>
                      <p className="text-xs text-gray-500 mb-2">
                        Aspect examples: {GUIDANCE[labels.dashboard_word].aspect.examples.join(', ')}
                      </p>

                      <AccordionTrigger className="py-2 text-sm">
                        Focus Areas ({aspect.focusAreas.length})
                      </AccordionTrigger>
                      <AccordionContent>
                        <div className="pl-4 space-y-2">
                          {aspect.focusAreas.map((focusArea, focusAreaIndex) => (
                            <div key={focusAreaIndex} className="flex items-center gap-2">
                              <Input
                                value={focusArea}
                                onChange={(e) => handleFocusAreaChange(aspectIndex, focusAreaIndex, e.target.value)}
                                placeholder={`e.g., ${GUIDANCE[labels.dashboard_word].focusArea.examples[focusAreaIndex % GUIDANCE[labels.dashboard_word].focusArea.examples.length]}`}
                                className="flex-1"
                              />
                              <Button
                                type="button"
                                variant="ghost"
                                size="icon"
                                onClick={() => removeFocusArea(aspectIndex, focusAreaIndex)}
                                disabled={aspect.focusAreas.length === 1}
                                className="text-red-500 hover:text-red-700"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ))}
                          <p className="text-xs text-gray-500 mt-2">
                            Focus area examples: {GUIDANCE[labels.dashboard_word].focusArea.examples.slice(0, 3).join(', ')}
                          </p>
                          <Button
                            type="button"
                            variant="outline"
                            size="sm"
                            onClick={() => addFocusArea(aspectIndex)}
                            className="flex items-center text-blue-600 w-full mt-2"
                          >
                            <Plus className="h-4 w-4 mr-1" /> Add Focus Area
                          </Button>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>
              </div>
            </div>
            <DialogFooter className="mt-6">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : editingJob ? labels.dashboard_edit_btn : labels.dashboard_new_btn}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default J_Index;