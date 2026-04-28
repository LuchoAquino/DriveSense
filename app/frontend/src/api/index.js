/*
 * index.js
 * Collection of functions to interact with the backend API for the dashboard
 */

// Base URL of the API server
const API_BASE_URL = "http://127.0.0.1:8000";

/**
 * Fetch overall dashboard statistics
 * @returns {Promise<Object>} JSON object with counts for detected and pending infractions
 * @throws {Error} if the HTTP request fails
 */
export const fetchDashboardStats = async () => {
  // Send GET request to /api/dashboard/stats
  const response = await fetch(`${API_BASE_URL}/api/dashboard/stats`);

  // If the response status is not in the 200–299 range, throw an error
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  // Parse and return the JSON payload
  return response.json();
};

/**
 * Fetch infractions grouped by rule/type
 * @returns {Promise<Array>} Array of objects, each containing a rule name and count
 * @throws {Error} if the HTTP request fails
 */
export const fetchInfractionsByRule = async () => {
  const response = await fetch(`${API_BASE_URL}/api/dashboard/infractions_by_rule`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

/**
 * Fetch infractions count for each day (last 7 days)
 * @returns {Promise<Array>} Array of objects with day labels and counts
 * @throws {Error} if the HTTP request fails
 */
export const fetchInfractionsByDay = async () => {
  const response = await fetch(`${API_BASE_URL}/api/dashboard/infractions_by_day`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

/**
 * Fetch full list of all infractions (regardless of status)
 * @returns {Promise<Array>} Array of infraction objects
 * @throws {Error} if the HTTP request fails
 */
export const fetchAllInfractions = async () => {
  const response = await fetch(`${API_BASE_URL}/api/infractions`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

/**
 * Fetch only pending infractions awaiting review
 * @returns {Promise<Array>} Array of pending infraction objects
 * @throws {Error} if the HTTP request fails
 */
export const fetchPendingInfractions = async () => {
  const response = await fetch(`${API_BASE_URL}/api/infractions/pending`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

/**
 * Fetch only confirmed infractions
 * @returns {Promise<Array>} Array of confirmed infraction objects
 * @throws {Error} if the HTTP request fails
 */
export const fetchConfirmedInfractions = async () => {
  const response = await fetch(`${API_BASE_URL}/api/infractions/confirmed`);
  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }
  return response.json();
};

/**
 * Submit a review decision for a specific infraction
 * @param {string|number} infractionId - Unique identifier of the infraction
 * @param {Object} reviewData - Payload with review fields (e.g., { approved: true, comments: '...' })
 * @returns {Promise<Object>} Updated infraction object after review
 * @throws {Error} with detail message if the HTTP request fails
 */
export const reviewInfraction = async (infractionId, reviewData) => {
  // Send PUT request to update the infraction review
  const response = await fetch(`${API_BASE_URL}/api/infractions/${infractionId}/review`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',  // Indicate JSON payload
    },
    body: JSON.stringify(reviewData),      // Serialize reviewData into JSON
  });

  // If the update endpoint returns an error, parse error detail or fallback to status
  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  // Parse and return the updated infraction
  return response.json();
};

/**
 * Generate a PDF report for selected infractions.
 * @param {Array<number>} infractionIds - Array of infraction IDs to include in the report.
 * @returns {Promise<Blob>} The PDF file as a Blob.
 * @throws {Error} if the HTTP request fails.
 */
export const generatePdfReport = async (infractionIds) => {
  const response = await fetch(`${API_BASE_URL}/api/reports/generate-pdf`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ infraction_ids: infractionIds }),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.blob(); // Return as Blob for file download
};

/**
 * Send a PDF report via email.
 * @param {Object} emailData - Object containing recipient_email, subject, body, and infraction_ids.
 * @returns {Promise<Object>} Success message.
 * @throws {Error} if the HTTP request fails.
 */
export const sendReportEmail = async (emailData) => {
  const response = await fetch(`${API_BASE_URL}/api/reports/send-email`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(emailData),
  });

  if (!response.ok) {
    const errorData = await response.json();
    throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};
