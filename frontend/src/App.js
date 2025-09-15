// src/App.js - Simple Clerk Integration
import React from 'react';
import { ClerkProvider, SignedIn, SignedOut } from '@clerk/clerk-react';
// import VantageDashboard from './VantageDashboard';
import VantageDashboard from './VantageDashboardRefactored';
import LandingPage from './components/landing/LandingPage';

// Your Clerk publishable key from environment
const CLERK_PUBLISHABLE_KEY = process.env.REACT_APP_CLERK_PUBLISHABLE_KEY

function App() {
  return (
    <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY}>
      <div className="App">
        <SignedOut>
          {/* Show when user is NOT signed in */}
          <LandingPage />
        </SignedOut>
        
        <SignedIn>
          {/* Show when user IS signed in */}
          <VantageDashboard />
        </SignedIn>
      </div>
    </ClerkProvider>
  );
}

export default App;