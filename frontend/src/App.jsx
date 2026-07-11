import React, { useState, useEffect } from 'react';
import { CandidateService } from './services/CandidateService';
import { RequisitionService } from './services/RequisitionService';
import { InterviewService } from './services/InterviewService';
import { VoiceService } from './services/VoiceService';

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  
  // Lists
  const [candidates, setCandidates] = useState([]);
  const [requisitions, setRequisitions] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [voiceHistory, setVoiceHistory] = useState([]);
  
  // Selected Candidate for detailed view
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  
  // Forms & Actions State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  
  // JD Form
  const [jdRequirements, setJdRequirements] = useState('');
  
  // Candidate Form
  const [candidateForm, setCandidateForm] = useState({
    name: '',
    email: '',
    phone: '',
    resumeUrl: ''
  });
  
  // Scheduling Form
  const [schedulingData, setSchedulingData] = useState({
    availability: 'Monday and Wednesday afternoons, 2 PM to 5 PM',
    slots: 'July 15th: 1 PM - 3 PM, July 16th: 3 PM - 5 PM',
    voiceId: 'EXAVITQu4vr4xnSDxMaL' // Sarah
  });
  
  // Voice selection list
  const [availableVoices, setAvailableVoices] = useState([]);
  const [elevenLabsAgentId, setElevenLabsAgentId] = useState('');
  const [activeCallId, setActiveCallId] = useState('');
  const [callStatus, setCallStatus] = useState('');
  const [showWebWidget, setShowWebWidget] = useState(false);

  useEffect(() => {
    if (showWebWidget) {
      const script = document.createElement('script');
      script.src = 'https://elevenlabs.io/convai-widget/index.js';
      script.async = true;
      script.type = 'text/javascript';
      document.body.appendChild(script);
      return () => {
        try {
          document.body.removeChild(script);
        } catch (e) {}
      };
    }
  }, [showWebWidget]);

  useEffect(() => {
    fetchInitialData();
  }, []);

  const fetchInitialData = async () => {
    try {
      setLoading(true);
      const [cList, rList, iList, vList, voices, config] = await Promise.all([
        CandidateService.getCandidates(),
        RequisitionService.getRequisitions(),
        InterviewService.getInterviews(),
        VoiceService.getHistory(),
        VoiceService.getVoices(),
        VoiceService.getConfig()
      ]);
      setCandidates(cList);
      setRequisitions(rList);
      setInterviews(iList);
      setVoiceHistory(vList);
      setAvailableVoices(voices);
      if (config && config.agent_id) {
        setElevenLabsAgentId(config.agent_id);
      }
    } catch (err) {
      console.error(err);
      setError('Failed to fetch data from backend. Verify FastAPI server is running on port 8000.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCandidate = async (e) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError('');
      const newCand = await CandidateService.createCandidate(candidateForm);
      setCandidates([...candidates, newCand]);
      setCandidateForm({ name: '', email: '', phone: '', resumeUrl: '' });
      setSuccess('Candidate imported successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Error importing candidate.');
    } finally {
      setLoading(false);
    }
  };

  const handleParseJD = async (e) => {
    e.preventDefault();
    if (!jdRequirements.trim()) return;
    try {
      setLoading(true);
      setError('');
      const result = await RequisitionService.parseJD(jdRequirements);
      setRequisitions([...requisitions, result.requisition]);
      setJdRequirements('');
      setSuccess('Job Description parsed and requisition created!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Error parsing Job Description.');
    } finally {
      setLoading(false);
    }
  };

  const handleScheduleInterview = async (candidateId) => {
    try {
      setLoading(true);
      setError('');
      const result = await CandidateService.scheduleInterview(
        candidateId,
        schedulingData.availability,
        schedulingData.slots,
        schedulingData.voiceId
      );
      
      // Update selected candidate details
      const updatedCand = await CandidateService.getCandidateById(candidateId);
      setSelectedCandidate(updatedCand);
      
      // Refresh list
      const cList = await CandidateService.getCandidates();
      setCandidates(cList);
      
      setSuccess('Interview outreach generated and scheduled!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Error scheduling interview.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulateVoiceResponse = async (candidateId) => {
    try {
      setLoading(true);
      setError('');
      
      // Create a dummy audio blob to simulate audio upload
      const dummyAudioContent = new Uint8Array([82, 73, 70, 70, 36, 0, 0, 0, 87, 65, 86, 69]); // Minimal WAV header
      const blob = new Blob([dummyAudioContent], { type: 'audio/wav' });
      const file = new File([blob], 'response.wav', { type: 'audio/wav' });

      await CandidateService.evaluateScreening(candidateId, file);
      
      // Refresh candidate details
      const updatedCand = await CandidateService.getCandidateById(candidateId);
      setSelectedCandidate(updatedCand);
      
      // Refresh list
      const cList = await CandidateService.getCandidates();
      setCandidates(cList);
      
      setSuccess('Voice response transcribed and scored successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Error processing voice screening evaluation.');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateRetrospective = async (candidateId) => {
    try {
      setLoading(true);
      setError('');
      
      await CandidateService.generateRetrospective(candidateId);
      
      // Refresh candidate details
      const updatedCand = await CandidateService.getCandidateById(candidateId);
      setSelectedCandidate(updatedCand);
      
      // Refresh list
      const cList = await CandidateService.getCandidates();
      setCandidates(cList);
      
      setSuccess('Hiring retrospective compiled!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err) {
      setError('Error compiling candidate retrospective.');
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerPhoneCall = async () => {
    if (!selectedCandidate) return;
    
    const phoneCallingCode = selectedCandidate.phone?.primaryPhoneCallingCode || '';
    const phoneNumber = selectedCandidate.phone?.primaryPhoneNumber || selectedCandidate.phone || '';
    let phone = phoneNumber;
    if (phoneCallingCode && !phone.startsWith('+')) {
      phone = phoneCallingCode + phone;
    }

    if (!phone) {
      setError('Candidate has no phone number registered.');
      return;
    }
    if (!elevenLabsAgentId.trim()) {
      setError('Please provide an ElevenLabs Agent ID.');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      setCallStatus('Initiating outbound call...');
      const result = await CandidateService.triggerOutboundCall(
        selectedCandidate.id,
        phone,
        elevenLabsAgentId
      );
      
      if (result.call_id) {
        setActiveCallId(result.call_id);
        setCallStatus('Ringing / In progress');
        setSuccess(`Outbound call triggered successfully! Call ID: ${result.call_id}`);
      } else {
        setCallStatus('Failed to initiate');
        setError(result.message || 'Failed to start outbound call.');
      }
      
      // Refresh candidate details
      const updatedCand = await CandidateService.getCandidateById(selectedCandidate.id);
      setSelectedCandidate(updatedCand);
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Error triggering outbound call.');
      setCallStatus('Error occurred');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchCallEvaluation = async () => {
    if (!selectedCandidate || !activeCallId) return;
    try {
      setLoading(true);
      setError('');
      setCallStatus('Fetching transcript & evaluating...');
      
      const result = await CandidateService.fetchCallEvaluation(
        selectedCandidate.id,
        activeCallId
      );
      
      setCallStatus('Completed & Evaluated');
      setSuccess('Call transcript retrieved and evaluated successfully!');
      
      // Refresh candidate details
      const updatedCand = await CandidateService.getCandidateById(selectedCandidate.id);
      setSelectedCandidate(updatedCand);
      
      // Refresh pipeline list
      const cList = await CandidateService.getCandidates();
      setCandidates(cList);
      
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Error fetching call evaluation.');
      setCallStatus('Failed to retrieve evaluation');
    } finally {
      setLoading(false);
    }
  };

  const handleFetchWebMicEvaluation = async (candidateId, agentId) => {
    if (!candidateId || !agentId) return;
    try {
      setLoading(true);
      setError('');
      setCallStatus('Fetching browser mic transcript & evaluating...');
      
      const result = await CandidateService.fetchLatestWebTranscript(candidateId, agentId);
      
      setCallStatus('Completed & Evaluated');
      setSuccess('Browser mic conversation transcript retrieved and evaluated successfully!');
      
      // Refresh candidate details
      const updatedCand = await CandidateService.getCandidateById(candidateId);
      setSelectedCandidate(updatedCand);
      
      // Refresh pipeline list
      const cList = await CandidateService.getCandidates();
      setCandidates(cList);
      
      setTimeout(() => setSuccess(''), 4000);
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || 'Error fetching browser mic evaluation. Ensure ElevenLabs API key is valid.');
      setCallStatus('Failed to retrieve evaluation');
    } finally {
      setLoading(false);
    }
  };

  // Helper for score color classes
  const getScoreClass = (score) => {
    if (!score) return '';
    if (score >= 4.0) return 'score-high';
    if (score >= 2.5) return 'score-med';
    return 'score-low';
  };

  // Helper for status badge classes
  const getStatusBadgeClass = (status) => {
    if (!status) return 'badge-applied';
    const statusMap = {
      'APPLIED': 'badge-applied',
      'SCREENING': 'badge-screening',
      'INTERVIEW_SCHEDULED': 'badge-scheduled',
      'INTERVIEW_COMPLETED': 'badge-completed',
      'SHORLISTED': 'badge-shorlisted',
      'REJECTED': 'badge-rejected',
      'HIRED': 'badge-shorlisted'
    };
    return statusMap[status] || 'badge-applied';
  };

  const getLinkedJobDescription = () => {
    if (!selectedCandidate || !requisitions) return '';
    const linkedReqs = selectedCandidate.requisitions || [];
    if (linkedReqs.length > 0) {
      const targetReqId = linkedReqs[0].id || linkedReqs[0];
      const match = requisitions.find(r => r.id === targetReqId);
      if (match) {
        return match.jobDescription || '';
      }
    }
    return '';
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo">OC</div>
          <h1 className="brand-title">OpenClaw Recruiting</h1>
        </div>
        <nav className="nav-tabs">
          <button 
            className={`nav-tab ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={`nav-tab ${activeTab === 'requisitions' ? 'active' : ''}`}
            onClick={() => setActiveTab('requisitions')}
          >
            Job Board ({requisitions.length})
          </button>
          <button 
            className={`nav-tab ${activeTab === 'candidates' ? 'active' : ''}`}
            onClick={() => setActiveTab('candidates')}
          >
            Candidates ({candidates.length})
          </button>
          <button 
            className={`nav-tab ${activeTab === 'voice' ? 'active' : ''}`}
            onClick={() => setActiveTab('voice')}
          >
            Voice Engine
          </button>
        </nav>
      </header>

      {/* Notifications */}
      {error && (
        <div style={{ background: 'rgba(239, 68, 68, 0.15)', color: '#EF4444', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          {error}
        </div>
      )}
      {success && (
        <div style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10B981', padding: '1rem', borderRadius: '8px', marginBottom: '1.5rem', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
          {success}
        </div>
      )}

      {/* Content tabs */}
      {activeTab === 'dashboard' && (
        <div>
          <div className="dashboard-stats">
            <div className="glass-panel" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: '800', background: 'var(--accent-gradient)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                {candidates.length}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>Total Candidates</div>
            </div>
            <div className="glass-panel" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--color-info)' }}>
                {requisitions.length}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>Active Requisitions</div>
            </div>
            <div className="glass-panel" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--color-purple)' }}>
                {candidates.filter(c => c.interviewStatus === 'INTERVIEW_SCHEDULED').length}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>Screening Calls Active</div>
            </div>
            <div className="glass-panel" style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '2.5rem', fontWeight: '800', color: 'var(--color-success)' }}>
                {candidates.filter(c => c.interviewStatus === 'SHORLISTED').length}
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '0.25rem' }}>Shortlisted profiles</div>
            </div>
          </div>

          <div className="grid-cols-3">
            <div className="glass-panel" style={{ gridColumn: 'span 3' }}>
              <h2 style={{ marginBottom: '1rem', fontSize: '1.2rem' }}>Active Pipelines</h2>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {candidates.length === 0 ? (
                  <p style={{ color: 'var(--text-muted)' }}>No candidates registered in Twenty CRM yet.</p>
                ) : (
                  candidates.slice(0, 5).map((candidate) => (
                    <div 
                      key={candidate.id} 
                      className="list-item" 
                      style={{ cursor: 'pointer' }}
                      onClick={() => { setSelectedCandidate(candidate); setActiveTab('candidates'); }}
                    >
                      <div>
                        <div style={{ fontWeight: '650' }}>{candidate.name}</div>
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          {candidate.email?.primaryEmail || 'No Email'}
                        </div>
                        {candidate.requisitions && candidate.requisitions.length > 0 && (
                          <div style={{ fontSize: '0.78rem', color: 'var(--primary)', marginTop: '0.2rem', fontWeight: '500' }}>
                            Role: {candidate.requisitions[0].jobTitle}
                          </div>
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <span className={`badge ${getStatusBadgeClass(candidate.interviewStatus)}`}>
                          {candidate.interviewStatus || 'APPLIED'}
                        </span>
                        {candidate.overallScore && (
                          <div className={`score-badge ${getScoreClass(candidate.overallScore)}`} style={{ width: '32px', height: '32px', fontSize: '0.85rem' }}>
                            {candidate.overallScore}
                          </div>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {activeTab === 'requisitions' && (
        <div className="grid-cols-3">
          <div className="glass-panel" style={{ gridColumn: 'span 3' }}>
            <h2 style={{ marginBottom: '1.2rem' }}>Requisitions in Twenty CRM</h2>
            {requisitions.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No requisitions defined.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {requisitions.map((req) => (
                  <div key={req.id} className="glass-panel" style={{ background: 'rgba(255,255,255,0.02)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                      <h3 style={{ fontSize: '1.1rem' }}>{req.jobTitle}</h3>
                      <span className="badge badge-screening">{req.status}</span>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', fontSize: '0.85rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
                      <div><strong>Department:</strong> {req.department}</div>
                      <div><strong>Location:</strong> {req.location}</div>
                      <div><strong>Experience:</strong> {req.experience}</div>
                      <div><strong>Type:</strong> {req.employmentType}</div>
                    </div>
                    <div style={{ fontSize: '0.9rem', color: 'var(--text-primary)', borderTop: '1px solid var(--border-color)', paddingTop: '0.5rem' }}>
                      {req.jobDescription}
                    </div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '0.5rem' }}>
                      <strong>Skills required:</strong> {req.requiredSkills}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {activeTab === 'candidates' && (
        <div className="grid-cols-3">
          {/* Candidates Pipeline List */}
          <div className="glass-panel" style={{ gridColumn: selectedCandidate ? '1' : 'span 3' }}>
            <h2 style={{ marginBottom: '1.2rem' }}>Candidate List</h2>
            {candidates.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No candidates registered.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {candidates.map((cand) => (
                  <div 
                    key={cand.id} 
                    className={`list-item ${selectedCandidate?.id === cand.id ? 'active-item' : ''}`}
                    style={{ 
                      cursor: 'pointer',
                      borderColor: selectedCandidate?.id === cand.id ? 'var(--primary)' : 'var(--border-color)',
                      background: selectedCandidate?.id === cand.id ? 'rgba(99, 102, 241, 0.05)' : 'rgba(17, 24, 39, 0.4)'
                    }}
                    onClick={() => setSelectedCandidate(cand)}
                  >
                    <div>
                      <div style={{ fontWeight: '650' }}>{cand.name}</div>
                      <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                        {cand.email?.primaryEmail || 'No email'}
                      </div>
                      {cand.requisitions && cand.requisitions.length > 0 && (
                        <div style={{ fontSize: '0.78rem', color: 'var(--primary)', marginTop: '0.2rem', fontWeight: '500' }}>
                          Role: {cand.requisitions[0].jobTitle}
                        </div>
                      )}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                      <span className={`badge ${getStatusBadgeClass(cand.interviewStatus)}`}>
                        {cand.interviewStatus}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Selected Candidate Detailed Action Card */}
          {selectedCandidate && (
            <div className="glass-panel" style={{ gridColumn: 'span 2' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', borderBottom: '1px solid var(--border-color)', paddingBottom: '1rem', marginBottom: '1rem' }}>
                <div>
                  <h2 style={{ fontSize: '1.5rem' }}>{selectedCandidate.name}</h2>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                    Email: {selectedCandidate.email?.primaryEmail || 'N/A'} | Phone: {selectedCandidate.phone?.primaryPhoneNumber || 'N/A'}
                  </p>
                  {selectedCandidate.requisitions && selectedCandidate.requisitions.length > 0 ? (
                    <div style={{ display: 'inline-block', background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.2)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.82rem', marginBottom: '0.5rem' }}>
                      <strong>Target Role:</strong> {selectedCandidate.requisitions[0].jobTitle} ({selectedCandidate.requisitions[0].location || 'Remote'})
                    </div>
                  ) : (
                    <div style={{ display: 'inline-block', background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.15)', padding: '0.25rem 0.5rem', borderRadius: '4px', fontSize: '0.82rem', color: '#ef4444', marginBottom: '0.5rem' }}>
                      <strong>Target Role:</strong> No linked requisition in CRM
                    </div>
                  )}
                  <br />
                  {selectedCandidate.resumeUrl && (
                    <a href={selectedCandidate.resumeUrl} target="_blank" rel="noreferrer" style={{ fontSize: '0.85rem', color: 'var(--primary)' }}>
                      View Candidate Resume URL
                    </a>
                  )}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                  <span className={`badge ${getStatusBadgeClass(selectedCandidate.interviewStatus)}`}>
                    {selectedCandidate.interviewStatus}
                  </span>
                  {selectedCandidate.overallScore && (
                    <div className={`score-badge ${getScoreClass(selectedCandidate.overallScore)}`}>
                      {selectedCandidate.overallScore}
                    </div>
                  )}
                </div>
              </div>

              {/* Action Grid */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                
                {/* 1. Scheduling Block */}
                <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.01)', padding: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Step 1: Automated Outreach Invitation</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                    Trigger the Scheduling Agent to propose meeting times and generate an AI audio call invitation.
                  </p>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label">Candidate Availability</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        value={schedulingData.availability}
                        onChange={(e) => setSchedulingData({ ...schedulingData, availability: e.target.value })}
                      />
                    </div>
                    <div className="form-group" style={{ margin: 0 }}>
                      <label className="form-label">Interviewer Calendar Blocks</label>
                      <input 
                        type="text" 
                        className="form-input" 
                        value={schedulingData.slots}
                        onChange={(e) => setSchedulingData({ ...schedulingData, slots: e.target.value })}
                      />
                    </div>
                  </div>
                  <div className="form-group">
                    <label className="form-label">Invitation Caller Voice (ElevenLabs)</label>
                    <select 
                      className="form-select"
                      value={schedulingData.voiceId}
                      onChange={(e) => setSchedulingData({ ...schedulingData, voiceId: e.target.value })}
                    >
                      {availableVoices.map(v => (
                        <option key={v.id} value={v.id}>{v.name} ({v.category})</option>
                      ))}
                    </select>
                  </div>
                  <button 
                    className="btn btn-primary" 
                    onClick={() => handleScheduleInterview(selectedCandidate.id)}
                    disabled={loading}
                  >
                    Generate Invitation & Schedule
                  </button>
                </div>

                {/* 2. Screening Call Simulator */}
                <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.01)', padding: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Step 2: Real Voice Interview Screening</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1.2rem' }}>
                    Conduct a live voice interview with the candidate using ElevenLabs Conversational AI, or run a simulated screening.
                  </p>

                  <div className="form-group" style={{ marginBottom: '1.2rem' }}>
                    <label className="form-label">ElevenLabs Agent ID (from ElevenLabs Console)</label>
                    <input 
                      type="text" 
                      className="form-input" 
                      placeholder="e.g. 2sX4GZ3a..." 
                      value={elevenLabsAgentId}
                      onChange={(e) => setElevenLabsAgentId(e.target.value)}
                    />
                    {(!elevenLabsAgentId || elevenLabsAgentId.toLowerCase().includes('mock')) && (
                      <div style={{ color: '#F59E0B', fontSize: '0.8rem', marginTop: '0.5rem', background: 'rgba(245, 158, 11, 0.1)', padding: '0.5rem', borderRadius: '4px', border: '1px solid rgba(245, 158, 11, 0.3)', lineHeight: '1.4' }}>
                        ⚠️ Currently using a <strong>Mock Agent ID</strong>. Real phone calls and browser microphone tests will not connect to a real ElevenLabs voice session unless you replace this with a valid <strong>Conversational Agent ID</strong> from your ElevenLabs Console.
                      </div>
                    )}
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }}>
                    <div className="glass-panel" style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '1rem' }}>
                      <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Method A: Outbound Call (Phone)</h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                        Triggers a real phone call to the candidate's registered number.
                      </p>
                      <button 
                        className="btn btn-primary"
                        style={{ width: '100%', fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                        onClick={handleTriggerPhoneCall}
                        disabled={loading || selectedCandidate.interviewStatus === 'APPLIED' || !elevenLabsAgentId}
                      >
                        Call Candidate
                      </button>
                      
                      {activeCallId && (
                        <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', background: 'rgba(0,0,0,0.15)', padding: '0.5rem', borderRadius: '6px' }}>
                          <div><strong>Call ID:</strong> {activeCallId}</div>
                          <div style={{ color: 'var(--primary)', marginTop: '0.25rem' }}><strong>Status:</strong> {callStatus}</div>
                          <button 
                            className="btn btn-secondary" 
                            style={{ width: '100%', marginTop: '0.5rem', fontSize: '0.75rem', padding: '0.25rem' }}
                            onClick={handleFetchCallEvaluation}
                          >
                            Fetch Transcript & Evaluate
                          </button>
                        </div>
                      )}
                    </div>

                    <div className="glass-panel" style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '1rem' }}>
                      <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Method B: In-Browser Web Voice</h4>
                      <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                        Opens ElevenLabs widget to speak directly using your computer microphone.
                      </p>
                      <button 
                        className={`btn ${showWebWidget ? 'btn-secondary' : 'btn-primary'}`}
                        style={{ width: '100%', fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                        onClick={() => setShowWebWidget(!showWebWidget)}
                        disabled={loading || selectedCandidate.interviewStatus === 'APPLIED' || !elevenLabsAgentId}
                      >
                        {showWebWidget ? 'Hide Widget' : 'Open Browser Mic'}
                      </button>
                      
                      {showWebWidget && (
                        <div style={{ marginTop: '0.75rem', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.75rem', width: '100%' }}>
                          {/* Dynamically render widget */}
                          <elevenlabs-convai 
                            agent-id={elevenLabsAgentId}
                            dynamic-variables={JSON.stringify({
                              candidate_name: selectedCandidate?.name || 'Candidate',
                              job_description: getLinkedJobDescription() || 'Software Engineer position'
                            })}
                          ></elevenlabs-convai>
                          
                          <button 
                            className="btn btn-success"
                            style={{ width: '100%', fontSize: '0.85rem', padding: '0.5rem 1rem', marginTop: '0.5rem' }}
                            onClick={() => handleFetchWebMicEvaluation(selectedCandidate.id, elevenLabsAgentId)}
                            disabled={loading}
                          >
                            Fetch Web Mic Transcript & Evaluate
                          </button>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="glass-panel" style={{ background: 'rgba(255, 255, 255, 0.02)', border: '1px solid var(--border-color)', padding: '1rem', marginBottom: '1.5rem' }}>
                    <h4 style={{ fontSize: '0.95rem', marginBottom: '0.5rem', color: 'var(--text-primary)' }}>Method C: Simulation</h4>
                    <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                      Simulate candidate response instantly using mock audio data.
                    </p>
                    <button 
                      className="btn btn-secondary"
                      style={{ width: '100%', fontSize: '0.85rem', padding: '0.5rem 1rem' }}
                      onClick={() => handleSimulateVoiceResponse(selectedCandidate.id)}
                      disabled={loading || selectedCandidate.interviewStatus === 'APPLIED'}
                    >
                      Simulate Screening Response
                    </button>
                  </div>

                  {selectedCandidate.transcript && (
                    <div style={{ background: 'rgba(0,0,0,0.25)', padding: '1rem', borderRadius: '8px', border: '1px solid var(--border-color)', marginBottom: '1rem' }}>
                      <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', fontWeight: 'bold', marginBottom: '0.25rem' }}>Interview Transcript:</div>
                      <div style={{ fontSize: '0.95rem', color: 'var(--text-primary)', fontStyle: 'italic', marginBottom: '0.75rem' }}>"{selectedCandidate.transcript}"</div>
                      {selectedCandidate.sentiment && (
                        <div style={{ fontSize: '0.85rem', color: 'var(--primary)' }}>
                          Sentiment Analysis: <strong>{selectedCandidate.sentiment}</strong>
                        </div>
                      )}
                    </div>
                  )}

                  {selectedCandidate.interviewStatus === 'APPLIED' && (
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', justifyContent: 'center', marginTop: '0.5rem' }}>
                      * Propose meeting slot first to unlock real-time/simulated screening options.
                    </span>
                  )}
                </div>

                {/* 3. Retrospective Analysis */}
                <div className="glass-panel" style={{ background: 'rgba(255,255,255,0.01)', padding: '1rem' }}>
                  <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>Step 3: Interview Retrospective Recommendation</h3>
                  <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', marginBottom: '1rem' }}>
                    Trigger the Retrospective Agent to analyze feedback, scores, and compile a final Hiring Decision.
                  </p>
                  <button 
                    className="btn btn-primary"
                    onClick={() => handleGenerateRetrospective(selectedCandidate.id)}
                    disabled={loading || !selectedCandidate.transcript}
                  >
                    Compile Retrospective report
                  </button>
                  {!selectedCandidate.transcript && (
                    <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginLeft: '1rem' }}>
                      * Requires voice screening transcript to evaluate.
                    </span>
                  )}
                </div>

              </div>
            </div>
          )}
        </div>
      )}

      {activeTab === 'voice' && (
        <div className="glass-panel">
          <h2 style={{ marginBottom: '1.2rem' }}>Voice Call Logs & History</h2>
          <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
            Historical audio integrations and autonomous ElevenLabs call tracking registry.
          </p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {voiceHistory.length === 0 ? (
              <p style={{ color: 'var(--text-muted)' }}>No historical calls logged.</p>
            ) : (
              voiceHistory.map((call, index) => (
                <div key={index} className="list-item">
                  <div>
                    <div style={{ fontWeight: 'bold' }}>Call Session ID: {call.call_id}</div>
                    <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                      Date: {call.date} | Duration: {call.duration} seconds
                    </div>
                  </div>
                  <span className="badge badge-completed">Completed</span>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
