import { useState, useCallback } from 'react';
import useVantageAPI from './useVantageAPI';

const useOptimizedAOI = (initialAois = [], onToast) => {
  const [aois, setAois] = useState(initialAois);
  const [isProcessing, setIsProcessing] = useState(false);
  const { apiCall } = useVantageAPI();

  const addAOIOptimistic = useCallback((tempAOI) => {
    // Add temporary AOI with optimistic update
    const optimisticAOI = {
      ...tempAOI,
      id: `temp-${Date.now()}`,
      status: 'creating'
    };
    setAois(prev => [...prev, optimisticAOI]);
    return optimisticAOI.id;
  }, []);

  const createAOI = useCallback(async (formData) => {
    // Optimistic update
    const tempId = addAOIOptimistic({
      name: formData.name,
      description: formData.description,
      location_name: formData.location,
      classification: formData.classification,
      priority: formData.priority,
      color_code: formData.color,
      bbox_coordinates: formData.coords
    });

    setIsProcessing(true);
    
    try {
      const aoiData = {
        name: formData.name,
        description: formData.description,
        location_name: formData.location,
        bbox_coordinates: formData.coords,
        classification: formData.classification,
        priority: formData.priority,
        color_code: formData.color,
        monitoring_frequency: 'WEEKLY'
      };

      const response = await apiCall('/api/aoi', {
        method: 'POST',
        body: JSON.stringify(aoiData)
      });

      // First, update the temporary AOI with success status
      setAois(prev => prev.map(aoi => 
        aoi.id === tempId ? { ...aoi, status: 'created' } : aoi
      ));

      // Then reload from server to get complete data including baseline
      // Small delay to allow server-side baseline creation to complete
      setTimeout(async () => {
        try {
          const response = await apiCall('/api/aoi');
          // Handle both old and new response formats
          const aoiData = response.data?.areas_of_interest || response.areas_of_interest || response;
          setAois(aoiData || []);
        } catch (error) {
          console.error('Error reloading AOIs after creation:', error);
        }
      }, 1500);

      onToast?.showSuccess(`AOI "${formData.name}" created successfully!`);
      
      // Only reload user profile for token count
      return response;
    } catch (error) {
      // Remove optimistic update on error
      setAois(prev => prev.filter(aoi => aoi.id !== tempId));
      onToast?.showError(`Failed to create AOI: ${error.message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [apiCall, addAOIOptimistic, onToast]);

  const deleteAOI = useCallback(async (aoiId) => {
    const aoiToDelete = aois.find(aoi => aoi.id === aoiId);
    if (!aoiToDelete) return;

    // Optimistic update - mark as deleting
    setAois(prev => prev.map(aoi => 
      aoi.id === aoiId ? { ...aoi, status: 'deleting' } : aoi
    ));

    setIsProcessing(true);

    try {
      await apiCall(`/api/aoi/${aoiId}`, { method: 'DELETE' });
      
      // Remove from state
      setAois(prev => prev.filter(aoi => aoi.id !== aoiId));
      onToast?.showSuccess(`AOI "${aoiToDelete.name}" deleted successfully`);
    } catch (error) {
      // Revert optimistic update on error
      setAois(prev => prev.map(aoi => 
        aoi.id === aoiId ? { ...aoi, status: undefined } : aoi
      ));
      onToast?.showError(`Failed to delete AOI: ${error.message}`);
      throw error;
    } finally {
      setIsProcessing(false);
    }
  }, [aois, apiCall, onToast]);

  const runAnalysis = useCallback(async (aoiId, analysisType = 'baseline_comparison') => {
    const aoiToAnalyze = aois.find(aoi => aoi.id === aoiId);
    if (!aoiToAnalyze) return;

    // Mark AOI as analyzing
    setAois(prev => prev.map(aoi => 
      aoi.id === aoiId ? { ...aoi, status: 'analyzing' } : aoi
    ));

    try {
      const data = await apiCall(`/api/aoi/${aoiId}/run-analysis`, {
        method: 'POST',
        body: JSON.stringify({ analysis_type: analysisType })
      });

      // Remove analyzing status
      setAois(prev => prev.map(aoi => 
        aoi.id === aoiId ? { ...aoi, status: undefined } : aoi
      ));

      onToast?.showSuccess(`Analysis completed for "${aoiToAnalyze.name}"`);
      return data;
    } catch (error) {
      // Remove analyzing status on error
      setAois(prev => prev.map(aoi => 
        aoi.id === aoiId ? { ...aoi, status: undefined } : aoi
      ));

      // Provide more specific error messages based on the error type
      let errorMessage = error.message;
      if (error.message.includes('500')) {
        errorMessage = `Server error during analysis. Token was consumed - check your analysis history.`;
        onToast?.showError(errorMessage);
        // Also show instructional info
        onToast?.showInfo('Your token count has been updated. The analysis may have partially completed.');
      } else if (error.message.includes('not bound to a Session')) {
        errorMessage = `Database session error. Token consumed but analysis incomplete.`;
        onToast?.showError(errorMessage);
        onToast?.showInfo('This is a server issue. Your token balance has been updated.');
      } else {
        onToast?.showError(`Analysis failed for "${aoiToAnalyze.name}": ${errorMessage}`);
      }
      
      throw error;
    }
  }, [aois, apiCall, onToast]);

  const scheduleMonitoring = useCallback(async (aoiId, frequency) => {
    const aoiToSchedule = aois.find(aoi => aoi.id === aoiId);
    if (!aoiToSchedule) return;

    try {
      await apiCall(`/api/aoi/${aoiId}/schedule-monitoring`, {
        method: 'POST',
        body: JSON.stringify({ frequency, enabled: true })
      });
      
      onToast?.showSuccess(`Monitoring scheduled for "${aoiToSchedule.name}" (${frequency})`);
    } catch (error) {
      onToast?.showError(`Failed to schedule monitoring: ${error.message}`);
      throw error;
    }
  }, [aois, apiCall, onToast]);

  const loadAOIs = useCallback(async () => {
    try {
      const response = await apiCall('/api/aoi');
      console.log('🔍 loadAOIs response:', response);
      // Handle both old and new response formats
      const aoiData = response.data?.areas_of_interest || response.areas_of_interest || response;
      console.log('🔍 extracted aoiData:', aoiData);
      setAois(aoiData || []);
    } catch (error) {
      console.error('Error loading AOIs:', error);
      onToast?.showError('Failed to load AOIs');
      setAois([]);
    }
  }, [apiCall, onToast]);

  return {
    aois,
    setAois,
    isProcessing,
    createAOI,
    deleteAOI,
    runAnalysis,
    scheduleMonitoring,
    loadAOIs
  };
};

export default useOptimizedAOI;