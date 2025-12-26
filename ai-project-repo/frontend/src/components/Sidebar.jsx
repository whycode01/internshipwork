/* eslint-disable react/prop-types */
/* eslint-disable no-unused-vars */
import axios from 'axios';
import { ChevronLeft, ChevronRight, Loader2, Settings, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useLabels } from '../context/LabelsContext.jsx';

const API_BASE_URL = 'http://localhost:8000/api/config';

const Sidebar = ({ isOpen, toggleSidebar }) => {
  const location = useLocation();
  const { labels, switchLabels } = useLabels();
  const [showSettings, setShowSettings] = useState(false);
  const [configs, setConfigs] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const navigate = useNavigate();
  const [isAudit, setIsAudit] = useState(!location.pathname.startsWith('/jobs'));

  // Fetch all configurations
  const fetchConfigs = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_BASE_URL}/`);
      setConfigs(response.data);

      // Find the selected provider
      const selected = response.data.find(config => config.isSelected);
      if (selected) {
        setSelectedProvider(selected);
      }
    } catch (err) {
      setError('Failed to load configurations');
      console.error('Error fetching configs:', err);
    } finally {
      setLoading(false);
    }
  };

  // Set default provider
  const setDefaultProvider = async (providerName) => {
    setLoading(true);
    setError(null);
    setSaveSuccess(false);
    try {
      const response = await axios.post(`${API_BASE_URL}/${providerName}`);
      await fetchConfigs(); // Refresh Configs After Update
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000); // Clear success message after 3 seconds
    } catch (err) {
      setError('Failed to set default provider');
      console.error('Error setting default provider:', err);
    } finally {
      setLoading(false);
    }
  };

  // Update provider configuration
  const updateProviderConfig = async (providerName, configData) => {
    setLoading(true);
    setError(null);
    setSaveSuccess(false);
    try {
      const response = await axios.put(`${API_BASE_URL}/${providerName}`, configData);
      await fetchConfigs(); // Refresh configs after update
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000); // Clear success message after 3 seconds
    } catch (err) {
      setError('Failed to update provider configuration');
      console.error('Error updating provider config:', err);
    } finally {
      setLoading(false);
    }
  };

  const toggleSettings = () => {
    setShowSettings(!showSettings);
    if (!showSettings) {
      fetchConfigs();
    }
  };

  // Initialize with configurations from API
  useEffect(() => {
    const newIsAudit = !location.pathname.startsWith('/jobs');
    setIsAudit(newIsAudit);
    switchLabels(newIsAudit ? 'audit' : 'job');
  }, [location.pathname, switchLabels])

  useEffect(() => {
    if (showSettings) {
      fetchConfigs();
    }
  }, [showSettings]);

  const handleProviderSelect = (provider) => {
    setSelectedProvider(configs.find(config => config.provider === provider));
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    if (selectedProvider) {
      setSelectedProvider({
        ...selectedProvider,
        configJson: {
          ...selectedProvider.configJson,
          [name]: value
        }
      });
    }
  };

  const saveSettings = async () => {
    if (selectedProvider) {
      // Update the provider configuration only
      await updateProviderConfig(selectedProvider.provider, selectedProvider.configJson);
      // Don't close the settings modal
    }
  };

  const getProviderClass = (provider) => {
    if (!selectedProvider) return 'text-gray-600';
    return selectedProvider.provider === provider
      ? 'bg-blue-100 text-blue-600 border-b-2 border-blue-600'
      : 'text-gray-600';
  };

  return (
    <div className="relative">
      <div
        className={`fixed top-0 left-0 h-full bg-gray-800 text-white transition-all duration-300 ease-in-out ${isOpen ? 'w-64' : 'w-0'
          } flex flex-col`}
      >
        {/* Sidebar Header */}
        <div className="flex justify-between items-center p-4">
          <h2 className={`font-bold text-xl ${!isOpen && 'hidden'}`}>Audit AI</h2>
          <button onClick={toggleSidebar} className="text-white p-2 bg-gray-700 rounded-lg cursor-pointer">
            {isOpen ? <ChevronLeft size={24} /> : <ChevronRight size={24} />}
          </button>
        </div>

        {/* Navigation Link */}
        <nav className={`mt-4 flex-grow ${!isOpen && 'hidden'}`}>
            <Link
              to={isAudit ? '/audit' : '/jobs'}
              className={`block px-4 py-3 hover:bg-gray-700 transition-colors ${(location.pathname === "/" || location.pathname === "/audit" || location.pathname === "/jobs") ? 'bg-gray-700' : ''
                }`}
            >
              Dashboard
            </Link>
            
            {/* Policies link - only show for jobs section */}
            {!isAudit && (
              <Link
                to="/jobs/policies"
                className={`block px-4 py-3 hover:bg-gray-700 transition-colors ${location.pathname === "/jobs/policies" ? 'bg-gray-700' : ''
                  }`}
              >
                Policies Management
              </Link>
            )}
        </nav>

        {/* Label Switcher Dropdown */}
        {isOpen && (
          <div className="p-4 mt-2">
            <label className="text-sm text-gray-300 block mb-2">Select Process:</label>
            <select
              className="w-full bg-gray-700 text-white p-2 rounded-md"
              onChange={(e) => {
                const value = e.target.value;
                if (value == "job") {
                  setIsAudit(false);
                  switchLabels(value);
                  navigate("/jobs");
                } else if (value == "audit") {
                  setIsAudit(true);
                  switchLabels(value);
                  navigate("/audit");
                }
              }}
              value={
                isAudit
                  ? 'audit'
                  : 'job'
              }
            >
              <option value="audit">Lab Audit</option>
              <option value="job">Interview Audit</option>
            </select>
          </div>
        )}

        {/* Settings Button */}
        {isOpen && (
          <div className="p-4 mt-auto border-t border-gray-700">
            <button
              onClick={toggleSettings}
              className="flex items-center justify-center w-full bg-gray-700 hover:bg-gray-600 text-white p-2 rounded-md transition-colors"
            >
              <Settings size={18} className="mr-2" />
              <span>Settings</span>
            </button>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      {showSettings && isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-lg w-full max-w-md p-6 mx-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-xl font-bold text-gray-800">Model Settings</h3>
              <button onClick={toggleSettings} className="text-gray-500 hover:text-gray-700">
                <X size={24} />
              </button>
            </div>

            {loading && (
              <div className="flex justify-center p-4">
                <Loader2 className="animate-spin" size={24} />
              </div>
            )}

            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 p-2 mb-4 rounded">
                {error}
              </div>
            )}

            {saveSuccess && (
              <div className="bg-green-100 border border-green-400 text-green-700 p-2 mb-4 rounded">
                Settings saved successfully
              </div>
            )}

            {!loading && configs.length > 0 && (
              <>
                {/* Provider Tabs */}
                <div className="flex flex-wrap border-b mb-4">
                  {configs.map((config) => (
                    <button
                      key={config.provider}
                      className={`px-4 py-2 ${getProviderClass(config.provider)}`}
                      onClick={() => handleProviderSelect(config.provider)}
                    >
                      {config.provider}
                    </button>
                  ))}
                </div>

                {/* Settings Form */}
                {selectedProvider && (
                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Model</label>
                      <input
                        type="text"
                        name="model"
                        value={selectedProvider.configJson.model || ''}
                        onChange={handleInputChange}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Endpoint</label>
                      <input
                        type="text"
                        name="endpoint"
                        value={selectedProvider.configJson.endpoint || ''}
                        onChange={handleInputChange}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">API Key</label>
                      <input
                        type="password"
                        name="apiKey"
                        value={selectedProvider.configJson.apiKey || ''}
                        onChange={handleInputChange}
                        className="w-full p-2 border border-gray-300 rounded-md"
                      />
                    </div>

                    <div className="flex justify-between mt-6">
                      <button
                        onClick={saveSettings}
                        className="px-4 py-2 bg-teal-500 text-white rounded-md hover:bg-teal-600 transition-colors"
                      >
                        Save Settings
                      </button>
                      <button
                        onClick={() => setDefaultProvider(selectedProvider.provider)}
                        className={`px-4 py-2 ${selectedProvider.isSelected
                            ? 'bg-gray-300 text-gray-700 cursor-not-allowed'
                            : 'bg-blue-500 text-white hover:bg-blue-600'
                          } rounded-md transition-colors`}
                        disabled={selectedProvider.isSelected}
                      >
                        {selectedProvider.isSelected ? 'Selected' : 'Set as Default'}
                      </button>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Sidebar;