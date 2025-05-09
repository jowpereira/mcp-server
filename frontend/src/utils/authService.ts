// Service for handling token refresh and authentication state
import { fetchWithAuth } from './api';

interface TokenResponse {
  access_token: string;
  token_type: string;
}

class AuthService {
  private static refreshPromise: Promise<string | null> | null = null;

  /**
   * Refreshes the authentication token
   * @returns A promise that resolves to the new token or null if refresh failed
   */
  public static async refreshToken(): Promise<string | null> {
    // If there's already a refresh in progress, return that promise
    // This prevents multiple simultaneous refresh requests
    if (this.refreshPromise) {
      return this.refreshPromise;
    }

    const token = localStorage.getItem('mcp_token');
    if (!token) {
      return null;
    }

    // Create new promise for token refresh
    this.refreshPromise = (async () => {
      try {
        const response = await fetchWithAuth('/tools/refresh-token', token, {
          method: 'POST',
        });

        if (!response.ok) {
          // If unauthorized, clear the token
          if (response.status === 401) {
            localStorage.removeItem('mcp_token');
          }
          console.error('Error refreshing token:', response.status);
          return null;
        }

        const data: TokenResponse = await response.json();
        const newToken = data.access_token;

        // Clean up the token if needed
        const tokenValue = newToken.startsWith('Bearer ') 
          ? newToken.substring(7) 
          : newToken;
        
        // Save to localStorage
        localStorage.setItem('mcp_token', tokenValue);
        return tokenValue;
      } catch (error) {
        console.error('Unexpected error during token refresh:', error);
        return null;
      } finally {
        // Clear the promise once done
        this.refreshPromise = null;
      }
    })();

    return this.refreshPromise;
  }

  /**
   * Checks if the current token is valid or needs to be refreshed
   * @returns Promise<boolean> True if authenticated, false otherwise
   */
  public static async isAuthenticated(): Promise<boolean> {
    const token = localStorage.getItem('mcp_token');
    if (!token) {
      return false;
    }

    try {
      // Try to decode and check expiration
      const payloadBase64 = token.split('.')[1];
      const payload = JSON.parse(atob(payloadBase64));
      
      // If token expires in less than 5 minutes, refresh it
      const currentTime = Math.floor(Date.now() / 1000);
      if (payload.exp - currentTime < 300) { // 300 seconds = 5 minutes
        const newToken = await this.refreshToken();
        return !!newToken;
      }
      
      return true;
    } catch (error) {
      console.error('Error checking token validity:', error);
      return false;
    }
  }
}

export default AuthService;
