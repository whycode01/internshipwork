import axios from 'axios';
import { AlertCircle, ChevronDown, Download, Edit, Loader2, Plus, Trash2, X } from 'lucide-react';
import { useEffect, useState } from 'react';

function Policies() {
  const [selectedType, setSelectedType] = useState('policies');
  const [selectedOption, setSelectedOption] = useState('');
  const [policyName, setPolicyName] = useState('');
  const [policyText, setPolicyText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [existingPolicies, setExistingPolicies] = useState([]);
  const [isEditing, setIsEditing] = useState(false);
  const [editingPolicyId, setEditingPolicyId] = useState('');

  const API_BASE_URL = 'http://localhost:8000/api/policies';

  const typeOptions = [
    { value: 'policies', label: 'Policies' },
    { value: 'report_templates', label: 'Report Templates' },
  ];

  // Load existing policies when component mounts or when type changes
  useEffect(() => {
    const loadPoliciesEffect = async () => {
      try {
        setIsLoading(true);
        const response = await axios.get(`${API_BASE_URL}/${selectedType}`);
        if (response.data.success) {
          setExistingPolicies(response.data.data);
        }
      } catch (err) {
        setError(`Failed to load ${selectedType}: ${err.response?.data?.detail || err.message}`);
      } finally {
        setIsLoading(false);
      }
    };
    
    loadPoliciesEffect();
  }, [selectedType]);

  const loadPolicies = async () => {
    try {
      setIsLoading(true);
      const response = await axios.get(`${API_BASE_URL}/${selectedType}`);
      if (response.data.success) {
        setExistingPolicies(response.data.data);
      }
    } catch (err) {
      setError(`Failed to load ${selectedType}: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    if (!policyName.trim() || !policyText.trim()) {
      setError('Please fill in both policy name and content');
      return;
    }

    try {
      setIsLoading(true);
      setError('');
      setSuccess('');

      if (isEditing) {
        // Update existing policy
        const response = await axios.put(`${API_BASE_URL}/${selectedType}/${editingPolicyId}`, {
          name: policyName,
          content: policyText
        });
        if (response.data.success) {
          setSuccess('Policy updated successfully!');
          setIsEditing(false);
          setEditingPolicyId('');
        }
      } else {
        // Create new policy
        const response = await axios.post(API_BASE_URL, {
          name: policyName,
          content: policyText,
          type: selectedType
        });
        if (response.data.success) {
          setSuccess('Policy saved successfully!');
        }
      }

      // Reset form
      setPolicyName('');
      setPolicyText('');
      setSelectedOption('');
      
      // Reload policies
      await loadPolicies();
    } catch (err) {
      setError(`Failed to save policy: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleEdit = (policy) => {
    setIsEditing(true);
    setEditingPolicyId(policy.id);
    setPolicyName(policy.name);
    setPolicyText(policy.content);
    setSelectedOption(policy.id);
    setError('');
    setSuccess('');
  };

  const handleDelete = async (policyId) => {
    if (!window.confirm('Are you sure you want to delete this policy?')) {
      return;
    }

    try {
      setIsLoading(true);
      const response = await axios.delete(`${API_BASE_URL}/${selectedType}/${policyId}`);
      if (response.data.success) {
        setSuccess('Policy deleted successfully!');
        await loadPolicies();
      }
    } catch (err) {
      setError(`Failed to delete policy: ${err.response?.data?.detail || err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = async (policyId) => {
    try {
      const response = await axios.get(`${API_BASE_URL}/${selectedType}/${policyId}/export`, {
        responseType: 'blob'
      });
      
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const policy = existingPolicies.find(p => p.id === policyId);
      link.setAttribute('download', `${policy?.name || 'policy'}_${policyId}.json`);
      
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(`Failed to export policy: ${err.response?.data?.detail || err.message}`);
    }
  };

  const handleCancel = () => {
    setIsEditing(false);
    setEditingPolicyId('');
    setPolicyName('');
    setPolicyText('');
    setSelectedOption('');
    setError('');
    setSuccess('');
  };

  const handleTypeChange = (newType) => {
    setSelectedType(newType);
    setSelectedOption('');
    setPolicyName('');
    setPolicyText('');
    setIsEditing(false);
    setEditingPolicyId('');
    setError('');
    setSuccess('');
  };

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-start py-10 px-4">
      {/* Header */}
      <div className="w-full max-w-4xl flex flex-col items-center mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">Policies Management</h1>
        <p className="text-lg text-gray-500">Configure and manage your system policies and report templates</p>
      </div>

      {/* Error/Success Messages */}
      {error && (
        <div className="w-full max-w-4xl mb-4">
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-center">
            <AlertCircle className="w-5 h-5 text-red-500 mr-3" />
            <span className="text-red-700">{error}</span>
          </div>
        </div>
      )}
      
      {success && (
        <div className="w-full max-w-4xl mb-4">
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 flex items-center">
            <div className="w-5 h-5 bg-green-500 rounded-full mr-3 flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-full"></div>
            </div>
            <span className="text-green-700">{success}</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="w-full max-w-4xl">
        <div className="bg-white rounded-xl shadow border p-8">
          <div className="space-y-6">
            {/* Form Fields Section */}
            <div className="space-y-6">
              {/* Document Type and Policy Selection */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Document Type Selection */}
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Document Type
                  </label>
                  <div className="relative">
                    <select
                      value={selectedType}
                      onChange={e => handleTypeChange(e.target.value)}
                      className="border border-gray-300 p-3 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white text-gray-900 font-medium"
                    >
                      {typeOptions.map(option => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                    <span className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    </span>
                  </div>
                </div>

                {/* Policy Selection */}
                <div className="space-y-2">
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    {selectedType === 'policies' ? 'Select Policy' : 'Select Template'}
                  </label>
                  <div className="relative">
                    <select
                      value={selectedOption}
                      onChange={e => {
                        const policyId = e.target.value;
                        setSelectedOption(policyId);
                        if (policyId) {
                          const policy = existingPolicies.find(p => p.id === policyId);
                          if (policy) {
                            handleEdit(policy);
                          }
                        }
                      }}
                      className="border border-gray-300 p-3 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 appearance-none bg-white text-gray-900 font-medium"
                    >
                      <option value="">Create New or Select Existing</option>
                      {existingPolicies.map(policy => (
                        <option key={policy.id} value={policy.id}>
                          {policy.name}
                        </option>
                      ))}
                    </select>
                    <span className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    </span>
                  </div>
                </div>
              </div>

              {/* Policy/Template Name Input */}
              <div className="space-y-2">
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  {selectedType === 'policies' ? 'Policy Name' : 'Template Name'}
                </label>
                <input
                  type="text"
                  value={policyName}
                  onChange={e => setPolicyName(e.target.value)}
                  className="border border-gray-300 p-3 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-white text-gray-900 font-medium"
                  placeholder={`Enter ${selectedType === 'policies' ? 'policy' : 'template'} name...`}
                />
              </div>
            </div>

            {/* Policy Details Section */}
            <div className="space-y-2">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                {selectedType === 'policies' ? 'Policy Details' : 'Template Content'}
              </label>
              <textarea
                value={policyText}
                onChange={e => setPolicyText(e.target.value)}
                rows={12}
                className="border border-gray-300 p-4 w-full rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none text-base min-h-[300px] bg-gray-50 focus:bg-white transition-colors"
                placeholder={`Write your ${selectedType === 'policies' ? 'policy details' : 'template content'} here...`}
              />
            </div>

            {/* Action Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 pt-6">
              <button 
                onClick={handleSave}
                disabled={isLoading}
                className="flex items-center justify-center gap-2 bg-black hover:bg-gray-900 text-white font-semibold px-6 py-3 rounded-lg transition duration-200 flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Plus className="w-4 h-4" />
                )}
                {isEditing ? 'Update Changes' : 'Save Changes'}
              </button>
              {selectedOption && (
                <button 
                  onClick={() => handleExport(selectedOption)}
                  className="flex items-center justify-center gap-2 border border-gray-300 rounded-lg px-6 py-3 font-semibold text-gray-700 hover:bg-gray-100 transition duration-200"
                >
                  <Download className="w-4 h-4" />
                  Export
                </button>
              )}
              <button 
                onClick={handleCancel}
                className="flex items-center justify-center gap-2 border border-gray-300 rounded-lg px-6 py-3 font-semibold text-gray-700 hover:bg-gray-100 transition duration-200"
              >
                <X className="w-4 h-4" />
                Cancel
              </button>
            </div>
          </div>
        </div>

        {/* Existing Policies List */}
        {existingPolicies.length > 0 && (
          <div className="mt-8 bg-white rounded-xl shadow border p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              Existing {selectedType === 'policies' ? 'Policies' : 'Templates'}
            </h2>
            <div className="space-y-4">
              {existingPolicies.map(policy => (
                <div key={policy.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-gray-900">{policy.name}</h3>
                      <p className="text-sm text-gray-500 mt-1">
                        Created: {new Date(policy.created_at).toLocaleDateString()} | 
                        Updated: {new Date(policy.updated_at).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        {policy.content.length > 100 
                          ? `${policy.content.substring(0, 100)}...` 
                          : policy.content
                        }
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <button
                        onClick={() => handleEdit(policy)}
                        className="p-2 text-blue-600 hover:bg-blue-50 rounded-lg transition duration-200"
                        title="Edit"
                      >
                        <Edit className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleExport(policy.id)}
                        className="p-2 text-green-600 hover:bg-green-50 rounded-lg transition duration-200"
                        title="Export"
                      >
                        <Download className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(policy.id)}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition duration-200"
                        title="Delete"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Policies;