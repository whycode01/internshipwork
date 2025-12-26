import { useState } from 'react';
import { ErrorBoundary } from 'react-error-boundary';
import { Navigate, Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar';

// JOBS
import J_Candidates_Edit from './components/Edit';
import J_Index from './components/Index';
import J_Candidates_Screening from './components/Manage';
import J_Candidates_New from './components/New';
import Policies from './components/Policies';
import J_Candidates from './components/ViewAll';

// Error Fallback Component
// eslint-disable-next-line react/prop-types
function ErrorFallback({error, resetErrorBoundary}) {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white shadow-lg rounded-lg p-6">
        <div className="flex items-center justify-center w-12 h-12 mx-auto bg-red-100 rounded-full">
          <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.5 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
          </svg>
        </div>
        <div className="mt-3 text-center">
          <h3 className="text-lg font-medium text-gray-900">Something went wrong</h3>
          <div className="mt-2">
            <p className="text-sm text-gray-500">
              An error occurred while loading the component.
            </p>
          </div>
          <div className="mt-4">
            <button
              type="button"
              className="inline-flex justify-center px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
              onClick={resetErrorBoundary}
            >
              Try again
            </button>
          </div>
          {error && (
            <details className="mt-4 text-left">
              <summary className="text-sm font-medium text-gray-900 cursor-pointer">Error details</summary>
              <pre className="mt-2 text-xs text-gray-600 bg-gray-50 p-2 rounded overflow-auto">
                {/* eslint-disable-next-line react/prop-types */}
                {error?.message || 'Unknown error occurred'}
              </pre>
            </details>
          )}
        </div>
      </div>
    </div>
  );
}

// Main App Component
const App = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };
  
  return (
    <Router>
        <Sidebar isOpen={isSidebarOpen} toggleSidebar={toggleSidebar} />
        <div className={`flex-1 transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-8'}`}>
          <Routes>
            <Route path="/" element={<Navigate to="/audit" replace />} />
            {/* <Route path="/dash" element={<Dash />} />
            <Route path="/case-creation" element={<CaseCreation />} />
            <Route path="/generate-questionnare" element={<GenerateQuestionnare />} />
            <Route path="/generate-crossq" element={<GenerateCrossQ />} />
            <Route path="/generate-report" element={<GenerateReport />} />
            <Route path="/view-reports" element={<ViewReports />} /> */}

            <Route path="/audit" element={<J_Index />} />
            <Route path="/audit/labs" element={<J_Candidates />} />
            <Route path="/audit/labs/new" element={<J_Candidates_New />} />
            <Route path="/audit/labs/manage" element={
              <ErrorBoundary 
                FallbackComponent={ErrorFallback}
                onReset={() => window.location.reload()}
              >
                <J_Candidates_Screening />
              </ErrorBoundary>
            } />

            <Route path="/jobs" element={<J_Index />} />
            <Route path="/jobs/policies" element={<Policies />} />
            <Route path="/jobs/candidates" element={<J_Candidates />} />
            <Route path="/jobs/candidates/new" element={<J_Candidates_New />} />
            <Route path="/jobs/candidates/screening" element={
              <ErrorBoundary 
                FallbackComponent={ErrorFallback}
                onReset={() => window.location.reload()}
              >
                <J_Candidates_Screening />
              </ErrorBoundary>
            } />
            <Route path="/jobs/candidates/edit" element={<J_Candidates_Edit />} />
          </Routes>
        </div>
    </Router>
  );
};

export default App;