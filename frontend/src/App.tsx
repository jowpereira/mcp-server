import AppRouter from './AppRouter';
import Navbar from './components/Navbar';
import { ErrorProvider, ErrorToast, ErrorBoundary } from './contexts/ErrorContext';
import './App.css';

function App() {
  return (
    <ErrorProvider>
      <ErrorBoundary>
        <Navbar />
        <div className="container">
          <AppRouter />
        </div>
        <ErrorToast />
      </ErrorBoundary>
    </ErrorProvider>
  );
}

export default App;
