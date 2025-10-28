import React, { useState, useEffect, useCallback } from 'react';
import DailyIframe from '@daily-co/daily-js';
import { Button } from "@/components/ui/button";
import { Phone, PhoneOff, Mic, MicOff, Volume2, Headphones, Settings } from "lucide-react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import axios from "axios";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Singleton call object to prevent duplicate instances
let sharedCallObject = null;

export default function VoiceChat() {
  const [callObject, setCallObject] = useState(null);
  const [callState, setCallState] = useState('idle'); // idle, joining, joined, leaving, left
  const [participants, setParticipants] = useState({});
  const [isMuted, setIsMuted] = useState(false);
  const [audioLevels, setAudioLevels] = useState({});
  const [roomUrl, setRoomUrl] = useState(null);
  const [meetingToken, setMeetingToken] = useState(null);
  const [audioDevices, setAudioDevices] = useState({ input: [], output: [] });
  const [selectedInputDevice, setSelectedInputDevice] = useState('default');
  const [selectedOutputDevice, setSelectedOutputDevice] = useState('default');
  const [showDeviceSettings, setShowDeviceSettings] = useState(false);

  // Initialize call object (singleton)
  useEffect(() => {
    if (!sharedCallObject) {
      sharedCallObject = DailyIframe.createCallObject({
        audioSource: true,
        videoSource: false,
      });
    }
    setCallObject(sharedCallObject);

    // Request microphone permissions to enumerate devices
    requestDevicePermissions();

    return () => {
      // Don't destroy the call object on unmount to preserve state
    };
  }, []);

  // Request device permissions and enumerate devices
  const requestDevicePermissions = async () => {
    try {
      // Request permissions
      await navigator.mediaDevices.getUserMedia({ audio: true });
      // Enumerate devices after permission granted
      enumerateAudioDevices();
    } catch (error) {
      console.error('Failed to get device permissions:', error);
    }
  };

  // Enumerate audio devices
  const enumerateAudioDevices = async () => {
    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const audioInputs = devices.filter(device => device.kind === 'audioinput');
      const audioOutputs = devices.filter(device => device.kind === 'audiooutput');
      
      setAudioDevices({
        input: audioInputs,
        output: audioOutputs
      });

      // Set default devices if not already set
      if (audioInputs.length > 0 && selectedInputDevice === 'default') {
        setSelectedInputDevice(audioInputs[0].deviceId);
      }
      if (audioOutputs.length > 0 && selectedOutputDevice === 'default') {
        setSelectedOutputDevice(audioOutputs[0].deviceId);
      }
    } catch (error) {
      console.error('Failed to enumerate devices:', error);
    }
  };

  // Listen for device changes (e.g., Bluetooth connected/disconnected)
  useEffect(() => {
    const handleDeviceChange = () => {
      enumerateAudioDevices();
      toast.info('Audio devices updated');
    };

    navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange);

    return () => {
      navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange);
    };
  }, []);

  // Set up event listeners
  useEffect(() => {
    if (!callObject) return;

    const events = {
      'joined-meeting': handleJoinedMeeting,
      'left-meeting': handleLeftMeeting,
      'participant-joined': handleParticipantUpdate,
      'participant-updated': handleParticipantUpdate,
      'participant-left': handleParticipantUpdate,
      'error': handleError,
    };

    Object.entries(events).forEach(([event, handler]) => {
      callObject.on(event, handler);
    });

    return () => {
      Object.keys(events).forEach((event) => {
        callObject.off(event, events[event]);
      });
    };
  }, [callObject]);

  // Audio level observer
  useEffect(() => {
    if (!callObject || callState !== 'joined') return;

    try {
      callObject.startRemoteParticipantsAudioLevelObserver(200);
      
      const handleAudioLevel = (event) => {
        if (event?.participantsAudioLevel) {
          setAudioLevels(event.participantsAudioLevel);
        }
      };

      callObject.on('remote-participants-audio-level', handleAudioLevel);

      return () => {
        callObject.off('remote-participants-audio-level', handleAudioLevel);
        try {
          callObject.stopRemoteParticipantsAudioLevelObserver();
        } catch (error) {
          console.error('Error stopping audio observer:', error);
        }
      };
    } catch (error) {
      console.error('Error starting audio observer:', error);
    }
  }, [callObject, callState]);

  const handleJoinedMeeting = useCallback(() => {
    setCallState('joined');
    setParticipants(callObject.participants());
    toast.success('Joined voice chat');
  }, [callObject]);

  const handleLeftMeeting = useCallback(() => {
    setCallState('left');
    setParticipants({});
    setRoomUrl(null);
    setMeetingToken(null);
    toast.info('Left voice chat');
  }, []);

  const handleParticipantUpdate = useCallback(() => {
    if (callObject) {
      setParticipants(callObject.participants());
    }
  }, [callObject]);

  const handleError = useCallback((event) => {
    console.error('Daily error:', event);
    toast.error('Voice chat error: ' + (event.error?.msg || 'Unknown error'));
  }, []);

  const joinCall = async () => {
    try {
      setCallState('joining');
      const token = localStorage.getItem("token");
      const username = localStorage.getItem("username");

      // Get or create room
      const roomResponse = await axios.post(
        `${API}/voice/room`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      // Get meeting token
      const tokenResponse = await axios.post(
        `${API}/voice/token`,
        {
          room_name: roomResponse.data.room_name,
          user_name: username,
          is_owner: true
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setRoomUrl(tokenResponse.data.room_url);
      setMeetingToken(tokenResponse.data.token);

      // Join the call with selected audio device
      await callObject.join({
        url: tokenResponse.data.room_url,
        token: tokenResponse.data.token,
        audioSource: selectedInputDevice !== 'default' ? { deviceId: selectedInputDevice } : true,
      });

      // Set output device after joining
      if (selectedOutputDevice !== 'default') {
        await callObject.setOutputDevice({ outputDeviceId: selectedOutputDevice });
      }

    } catch (error) {
      console.error('Failed to join call:', error);
      toast.error('Failed to join voice chat');
      setCallState('idle');
    }
  };

  const leaveCall = async () => {
    try {
      setCallState('leaving');
      await callObject.leave();
    } catch (error) {
      console.error('Failed to leave call:', error);
      toast.error('Failed to leave voice chat');
      setCallState('idle');
    }
  };

  const toggleMute = async () => {
    try {
      const newState = !isMuted;
      await callObject.setLocalAudio(!newState);
      setIsMuted(newState);
    } catch (error) {
      console.error('Failed to toggle mute:', error);
      toast.error('Failed to toggle mute');
    }
  };

  // Change input device
  const changeInputDevice = async (deviceId) => {
    try {
      setSelectedInputDevice(deviceId);
      if (callState === 'joined' && callObject) {
        await callObject.setInputDevicesAsync({
          audioDeviceId: deviceId
        });
        toast.success('Microphone changed');
      }
    } catch (error) {
      console.error('Failed to change input device:', error);
      toast.error('Failed to change microphone');
    }
  };

  // Change output device
  const changeOutputDevice = async (deviceId) => {
    try {
      setSelectedOutputDevice(deviceId);
      if (callState === 'joined' && callObject) {
        await callObject.setOutputDevice({ outputDeviceId: deviceId });
        toast.success('Speaker changed');
      }
    } catch (error) {
      console.error('Failed to change output device:', error);
      toast.error('Failed to change speaker');
    }
  };

  const getAudioIndicator = (sessionId) => {
    const level = audioLevels[sessionId] || 0;
    const opacity = level > 0 ? Math.min(level / 0.08, 1) : 0;
    return opacity;
  };

  const participantsList = Object.values(participants);
  const participantCount = participantsList.length;

  if (callState === 'idle' || callState === 'left') {
    return (
      <div className="voice-chat-container bg-slate-800/50 rounded-lg p-4 border border-slate-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Phone className="w-5 h-5 text-green-400" />
            <h3 className="text-lg font-semibold text-slate-100">Voice Chat</h3>
          </div>
          {participantCount > 0 && (
            <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">
              {participantCount} in call
            </span>
          )}
        </div>
        <p className="text-sm text-slate-400 mb-4">
          Join the admin voice chat to talk with other admins in real-time.
        </p>

        {/* Device Selection */}
        <div className="mb-4 space-y-3">
          <Button
            onClick={() => setShowDeviceSettings(!showDeviceSettings)}
            variant="outline"
            size="sm"
            className="w-full border-slate-600 text-slate-300 hover:bg-slate-700"
          >
            <Settings className="w-4 h-4 mr-2" />
            {showDeviceSettings ? 'Hide' : 'Show'} Audio Settings
          </Button>

          {showDeviceSettings && (
            <div className="space-y-3 p-3 bg-slate-900/50 rounded-lg">
              <div>
                <label className="text-xs text-slate-400 mb-1 block flex items-center gap-1">
                  <Mic className="w-3 h-3" />
                  Microphone
                </label>
                <Select value={selectedInputDevice} onValueChange={changeInputDevice}>
                  <SelectTrigger className="w-full bg-slate-800 border-slate-600 text-slate-200">
                    <SelectValue placeholder="Select microphone" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-600">
                    {audioDevices.input.map((device) => (
                      <SelectItem 
                        key={device.deviceId} 
                        value={device.deviceId}
                        className="text-slate-200 hover:bg-slate-700"
                      >
                        {device.label || `Microphone ${device.deviceId.substring(0, 8)}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <label className="text-xs text-slate-400 mb-1 block flex items-center gap-1">
                  <Headphones className="w-3 h-3" />
                  Speaker / Headphones
                </label>
                <Select value={selectedOutputDevice} onValueChange={changeOutputDevice}>
                  <SelectTrigger className="w-full bg-slate-800 border-slate-600 text-slate-200">
                    <SelectValue placeholder="Select speaker" />
                  </SelectTrigger>
                  <SelectContent className="bg-slate-800 border-slate-600">
                    {audioDevices.output.map((device) => (
                      <SelectItem 
                        key={device.deviceId} 
                        value={device.deviceId}
                        className="text-slate-200 hover:bg-slate-700"
                      >
                        {device.label || `Speaker ${device.deviceId.substring(0, 8)}`}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <p className="text-xs text-slate-500 italic">
                💡 Bluetooth devices will appear here when connected
              </p>
            </div>
          )}
        </div>

        <Button
          onClick={joinCall}
          disabled={callState === 'joining'}
          className="w-full bg-green-600 hover:bg-green-700 text-white"
        >
          <Phone className="w-4 h-4 mr-2" />
          {callState === 'joining' ? 'Joining...' : 'Join Voice Chat'}
        </Button>
      </div>
    );
  }

  if (callState === 'joining' || callState === 'leaving') {
    return (
      <div className="voice-chat-container bg-slate-800/50 rounded-lg p-4 border border-slate-700">
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400 mx-auto mb-3"></div>
          <p className="text-slate-300">
            {callState === 'joining' ? 'Joining voice chat...' : 'Leaving voice chat...'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="voice-chat-container bg-slate-800/50 rounded-lg p-4 border border-slate-700">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Phone className="w-5 h-5 text-green-400" />
          <h3 className="text-lg font-semibold text-slate-100">Voice Chat Active</h3>
        </div>
        <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">
          {participantCount + 1} connected
        </span>
      </div>

      {/* Controls */}
      <div className="space-y-2 mb-4">
        <div className="flex gap-2">
          <Button
            onClick={toggleMute}
            variant="outline"
            size="sm"
            className={`flex-1 ${
              isMuted 
                ? 'bg-red-500/20 border-red-500 text-red-400 hover:bg-red-500/30' 
                : 'bg-slate-700 border-slate-600 text-slate-200 hover:bg-slate-600'
            }`}
          >
            {isMuted ? (
              <>
                <MicOff className="w-4 h-4 mr-2" />
                Unmute
              </>
            ) : (
              <>
                <Mic className="w-4 h-4 mr-2" />
                Mute
              </>
            )}
          </Button>
          <Button
            onClick={leaveCall}
            variant="outline"
            size="sm"
            className="flex-1 bg-red-500/20 border-red-500 text-red-400 hover:bg-red-500/30"
          >
            <PhoneOff className="w-4 h-4 mr-2" />
            Leave
          </Button>
        </div>

        {/* Device Settings Toggle */}
        <Button
          onClick={() => setShowDeviceSettings(!showDeviceSettings)}
          variant="outline"
          size="sm"
          className="w-full border-slate-600 text-slate-300 hover:bg-slate-700"
        >
          <Settings className="w-4 h-4 mr-2" />
          {showDeviceSettings ? 'Hide' : 'Change'} Audio Devices
        </Button>

        {showDeviceSettings && (
          <div className="space-y-3 p-3 bg-slate-900/50 rounded-lg">
            <div>
              <label className="text-xs text-slate-400 mb-1 block flex items-center gap-1">
                <Mic className="w-3 h-3" />
                Microphone
              </label>
              <Select value={selectedInputDevice} onValueChange={changeInputDevice}>
                <SelectTrigger className="w-full bg-slate-800 border-slate-600 text-slate-200">
                  <SelectValue placeholder="Select microphone" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {audioDevices.input.map((device) => (
                    <SelectItem 
                      key={device.deviceId} 
                      value={device.deviceId}
                      className="text-slate-200 hover:bg-slate-700"
                    >
                      {device.label || `Microphone ${device.deviceId.substring(0, 8)}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-xs text-slate-400 mb-1 block flex items-center gap-1">
                <Headphones className="w-3 h-3" />
                Speaker / Headphones
              </label>
              <Select value={selectedOutputDevice} onValueChange={changeOutputDevice}>
                <SelectTrigger className="w-full bg-slate-800 border-slate-600 text-slate-200">
                  <SelectValue placeholder="Select speaker" />
                </SelectTrigger>
                <SelectContent className="bg-slate-800 border-slate-600">
                  {audioDevices.output.map((device) => (
                    <SelectItem 
                      key={device.deviceId} 
                      value={device.deviceId}
                      className="text-slate-200 hover:bg-slate-700"
                    >
                      {device.label || `Speaker ${device.deviceId.substring(0, 8)}`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <p className="text-xs text-slate-500 italic">
              💡 Switch to Bluetooth devices on-the-fly
            </p>
          </div>
        )}
      </div>

      {/* Participants */}
      <div className="space-y-2">
        <h4 className="text-sm font-medium text-slate-300 mb-2">Participants:</h4>
        
        {/* Local participant */}
        <div className="flex items-center justify-between bg-slate-900/50 rounded p-2">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white text-sm font-semibold">
              {localStorage.getItem("username")?.charAt(0).toUpperCase()}
            </div>
            <span className="text-sm text-slate-200">
              {localStorage.getItem("username")} (You)
            </span>
          </div>
          <div className="flex items-center gap-2">
            {!isMuted && (
              <Volume2 className="w-4 h-4 text-green-400 animate-pulse" />
            )}
            {isMuted && <MicOff className="w-4 h-4 text-red-400" />}
          </div>
        </div>

        {/* Remote participants */}
        {participantsList.map((participant) => {
          const audioOpacity = getAudioIndicator(participant.session_id);
          return (
            <div
              key={participant.session_id}
              className="flex items-center justify-between bg-slate-900/50 rounded p-2"
            >
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 rounded-full bg-slate-600 flex items-center justify-center text-white text-sm font-semibold">
                  {participant.user_name?.charAt(0).toUpperCase() || '?'}
                </div>
                <span className="text-sm text-slate-200">
                  {participant.user_name || 'Anonymous'}
                </span>
              </div>
              <div className="flex items-center gap-2">
                {participant.audio && audioOpacity > 0.3 && (
                  <Volume2 
                    className="w-4 h-4 text-green-400" 
                    style={{ opacity: audioOpacity }}
                  />
                )}
                {!participant.audio && <MicOff className="w-4 h-4 text-red-400" />}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
