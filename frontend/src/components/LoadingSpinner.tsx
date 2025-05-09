import React from 'react';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  fullPage?: boolean;
  message?: string;
}

const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'medium',
  color = '#4071b8',
  fullPage = false,
  message
}) => {
  // Tamanho do spinner baseado na prop size
  let dimensions = '40px';
  let borderWidth = '4px';
  
  if (size === 'small') {
    dimensions = '20px';
    borderWidth = '2px';
  } else if (size === 'large') {
    dimensions = '60px';
    borderWidth = '6px';
  }
  
  const spinnerStyle: React.CSSProperties = {
    width: dimensions,
    height: dimensions,
    border: `${borderWidth} solid rgba(0, 0, 0, 0.1)`,
    borderTopColor: color,
    borderRadius: '50%',
    animation: 'spin 1s linear infinite',
  };
  
  const containerStyle: React.CSSProperties = fullPage
    ? {
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: 'rgba(255, 255, 255, 0.8)',
        zIndex: 1000,
      }
    : {
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '20px',
      };

  const messageStyle: React.CSSProperties = {
    marginTop: '10px',
    color: '#333',
    fontWeight: 'bold',
  };

  return (
    <div style={containerStyle} className="loading-spinner-container">
      <div style={spinnerStyle} className="loading-spinner"></div>
      {message && <div style={messageStyle}>{message}</div>}
      
      {/* Define a animação via CSS */}
      <style>
        {`
          @keyframes spin {
            0% {
              transform: rotate(0deg);
            }
            100% {
              transform: rotate(360deg);
            }
          }
        `}
      </style>
    </div>
  );
};

export default LoadingSpinner;
