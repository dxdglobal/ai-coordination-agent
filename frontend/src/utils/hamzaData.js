// Real Database Integration - No Mock Data
// This file has been cleaned of all mock data
// All queries now go directly to the real CRM database

console.log('⚠️ hamzaData.js has been deprecated - using real database integration only');

// Legacy exports for backward compatibility (all return empty/redirect to real API)
export const hamzaProjectsData = {
  total: 0,
  active: 0,
  completed: 0,
  projects: [],
  message: "Mock data removed - using real database integration"
};

export const isHamzaQuery = () => {
  console.warn('isHamzaQuery deprecated - all queries now go to real database');
  return false;
};

export const isNawazQuery = () => {
  console.warn('isNawazQuery deprecated - all queries now go to real database');
  return false;
};

export const isDenizQuery = () => {
  console.warn('isDenizQuery deprecated - all queries now go to real database');
  return false;
};

export const generateHamzaResponse = () => {
  return "This function has been deprecated. All responses now come from the real CRM database via the API.";
};

export const generatePersonResponse = () => {
  return "This function has been deprecated. All responses now come from the real CRM database via the API.";
};

export const parseHamzaQuery = () => {
  console.warn('parseHamzaQuery deprecated - query parsing now handled by backend');
  return { type: 'deprecated', projects: [], tasks: [] };
};

// Export message for developers
export const DEPRECATION_MESSAGE = `
🚨 IMPORTANT: hamzaData.js has been completely cleaned of mock data.
All project and task queries now use real CRM database integration.
Please use the ChatReal component and real_crm_server.py backend.
`;

export default {
  hamzaProjectsData,
  DEPRECATION_MESSAGE
};