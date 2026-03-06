/**
 * NFC Card Manager Page
 * 
 * Program NTAG215 NFC cards with member profile URLs
 * for digital business cards. Uses Web NFC API (Chrome Android).
 */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { toast } from 'sonner';
import { 
  ArrowLeft, Smartphone, Wifi, WifiOff, CheckCircle2, 
  XCircle, Loader2, CreditCard, User, Link2, 
  AlertTriangle, Scan, PenTool, RefreshCw
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

export default function NFCManager() {
  const navigate = useNavigate();
  const [nfcSupported, setNfcSupported] = useState(null);
  const [nfcPermission, setNfcPermission] = useState(null);
  const [isScanning, setIsScanning] = useState(false);
  const [isWriting, setIsWriting] = useState(false);
  const [lastRead, setLastRead] = useState(null);
  const [writeSuccess, setWriteSuccess] = useState(null);
  
  // Members for linking
  const [members, setMembers] = useState([]);
  const [loadingMembers, setLoadingMembers] = useState(true);
  
  // Write form
  const [writeMode, setWriteMode] = useState('member'); // 'member' or 'custom'
  const [selectedMember, setSelectedMember] = useState('');
  const [customUrl, setCustomUrl] = useState('');
  
  // NFC Controller ref
  const abortControllerRef = useRef(null);
  
  const token = localStorage.getItem('token');

  useEffect(() => {
    checkNFCSupport();
    loadMembers();
    
    return () => {
      // Cleanup: abort any ongoing NFC operations
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const checkNFCSupport = async () => {
    if ('NDEFReader' in window) {
      setNfcSupported(true);
      // Check permission
      try {
        const permissionStatus = await navigator.permissions.query({ name: 'nfc' });
        setNfcPermission(permissionStatus.state);
        permissionStatus.onchange = () => {
          setNfcPermission(permissionStatus.state);
        };
      } catch (err) {
        // Permission API might not support NFC query
        setNfcPermission('prompt');
      }
    } else {
      setNfcSupported(false);
    }
  };

  const loadMembers = async () => {
    try {
      const res = await axios.get(`${API}/members`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMembers(res.data || []);
    } catch (err) {
      console.error('Error loading members:', err);
    } finally {
      setLoadingMembers(false);
    }
  };

  const getMemberProfileUrl = (memberId) => {
    // Generate the public profile URL for the member
    const baseUrl = window.location.origin;
    return `${baseUrl}/member/${memberId}`;
  };

  const handleReadNFC = async () => {
    if (!nfcSupported) {
      toast.error('NFC is not supported on this device/browser');
      return;
    }

    setIsScanning(true);
    setLastRead(null);
    
    try {
      abortControllerRef.current = new AbortController();
      const ndef = new window.NDEFReader();
      
      await ndef.scan({ signal: abortControllerRef.current.signal });
      toast.info('Hold your NFC card near the device...');

      ndef.onreading = (event) => {
        const { message, serialNumber } = event;
        
        let records = [];
        for (const record of message.records) {
          const decoder = new TextDecoder();
          let data = '';
          
          if (record.recordType === 'url') {
            data = decoder.decode(record.data);
          } else if (record.recordType === 'text') {
            data = decoder.decode(record.data);
          } else if (record.recordType === 'mime') {
            data = `MIME: ${record.mediaType}`;
          } else {
            data = `Type: ${record.recordType}`;
          }
          
          records.push({
            type: record.recordType,
            data: data
          });
        }
        
        setLastRead({
          serialNumber: serialNumber,
          records: records,
          timestamp: new Date().toLocaleString()
        });
        
        setIsScanning(false);
        toast.success('Card read successfully!');
        
        // Abort after successful read
        if (abortControllerRef.current) {
          abortControllerRef.current.abort();
        }
      };

      ndef.onreadingerror = () => {
        toast.error('Error reading NFC card. Try again.');
        setIsScanning(false);
      };

    } catch (err) {
      if (err.name === 'AbortError') {
        // Scan was cancelled
        return;
      }
      console.error('NFC Read Error:', err);
      toast.error(`NFC Error: ${err.message}`);
      setIsScanning(false);
    }
  };

  const handleWriteNFC = async () => {
    if (!nfcSupported) {
      toast.error('NFC is not supported on this device/browser');
      return;
    }

    let urlToWrite = '';
    
    if (writeMode === 'member') {
      if (!selectedMember) {
        toast.error('Please select a member');
        return;
      }
      urlToWrite = getMemberProfileUrl(selectedMember);
    } else {
      if (!customUrl) {
        toast.error('Please enter a URL');
        return;
      }
      // Ensure URL has protocol
      urlToWrite = customUrl.startsWith('http') ? customUrl : `https://${customUrl}`;
    }

    setIsWriting(true);
    setWriteSuccess(null);

    try {
      abortControllerRef.current = new AbortController();
      const ndef = new window.NDEFReader();
      
      toast.info('Hold your NFC card near the device to write...');

      await ndef.write(
        {
          records: [
            { recordType: 'url', data: urlToWrite }
          ]
        },
        { signal: abortControllerRef.current.signal }
      );

      setWriteSuccess({
        url: urlToWrite,
        timestamp: new Date().toLocaleString()
      });
      
      toast.success('NFC card programmed successfully!');
      
    } catch (err) {
      if (err.name === 'AbortError') {
        toast.info('Write cancelled');
        return;
      }
      console.error('NFC Write Error:', err);
      toast.error(`Write failed: ${err.message}`);
      setWriteSuccess(false);
    } finally {
      setIsWriting(false);
    }
  };

  const cancelOperation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setIsScanning(false);
    setIsWriting(false);
  };

  const selectedMemberData = members.find(m => m._id === selectedMember || m.id === selectedMember);

  // Browser not supported warning
  if (nfcSupported === false) {
    return (
      <div className="min-h-screen bg-slate-900 p-4">
        <div className="max-w-2xl mx-auto">
          <Button 
            variant="ghost" 
            onClick={() => navigate('/')}
            className="text-slate-400 hover:text-white mb-4"
          >
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Dashboard
          </Button>

          <Card className="bg-slate-800 border-slate-700">
            <CardHeader>
              <CardTitle className="text-red-400 flex items-center gap-2">
                <WifiOff className="w-6 h-6" />
                NFC Not Supported
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="text-white font-medium">Web NFC is not available</p>
                    <p className="text-slate-400 text-sm mt-1">
                      Web NFC is only supported on <strong>Chrome for Android</strong> (version 89+).
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-2 text-slate-400 text-sm">
                <p className="font-medium text-white">To use NFC card programming:</p>
                <ul className="list-disc list-inside space-y-1 ml-2">
                  <li>Use an Android device with NFC hardware</li>
                  <li>Open this page in Google Chrome browser</li>
                  <li>Ensure NFC is enabled in device settings</li>
                </ul>
              </div>

              <div className="pt-4 border-t border-slate-700">
                <p className="text-slate-500 text-xs">
                  Current browser: {navigator.userAgent.includes('Chrome') ? 'Chrome' : 'Not Chrome'} on {
                    /Android/i.test(navigator.userAgent) ? 'Android' : 
                    /iPhone|iPad/i.test(navigator.userAgent) ? 'iOS (not supported)' : 'Desktop'
                  }
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900">
      {/* Header */}
      <div className="bg-slate-800 border-b border-slate-700 px-3 sm:px-4 py-3 sm:py-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 sm:gap-4">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/')}
              className="text-slate-400 hover:text-white p-2 sm:px-3"
            >
              <ArrowLeft className="w-4 h-4 sm:mr-2" />
              <span className="hidden sm:inline">Dashboard</span>
            </Button>
            <div>
              <h1 className="text-lg sm:text-xl font-bold text-white flex items-center gap-2">
                <CreditCard className="w-5 h-5 sm:w-6 sm:h-6 text-blue-400" />
                NFC Card Manager
              </h1>
              <p className="text-slate-400 text-xs sm:text-sm">Program digital business cards</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto p-3 sm:p-4 space-y-4 sm:space-y-6">
        
        {/* NFC Status Card */}
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  nfcSupported ? 'bg-green-600/20' : 'bg-red-600/20'
                }`}>
                  {nfcSupported ? (
                    <Wifi className="w-5 h-5 text-green-400" />
                  ) : nfcSupported === false ? (
                    <WifiOff className="w-5 h-5 text-red-400" />
                  ) : (
                    <Loader2 className="w-5 h-5 text-slate-400 animate-spin" />
                  )}
                </div>
                <div>
                  <p className="text-white font-medium">NFC Status</p>
                  <p className="text-slate-400 text-sm">
                    {nfcSupported === null ? 'Checking...' :
                     nfcSupported ? 'Ready to use' : 'Not supported'}
                  </p>
                </div>
              </div>
              {nfcPermission && (
                <span className={`text-xs px-2 py-1 rounded ${
                  nfcPermission === 'granted' ? 'bg-green-900/50 text-green-400' :
                  nfcPermission === 'denied' ? 'bg-red-900/50 text-red-400' :
                  'bg-yellow-900/50 text-yellow-400'
                }`}>
                  {nfcPermission === 'granted' ? 'Permission Granted' :
                   nfcPermission === 'denied' ? 'Permission Denied' : 'Permission Required'}
                </span>
              )}
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
          
          {/* Read NFC Card */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-base sm:text-lg flex items-center gap-2">
                <Scan className="w-5 h-5 text-cyan-400" />
                Read Card
              </CardTitle>
              <CardDescription>
                Scan an NFC card to see its contents
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isScanning ? (
                <div className="text-center py-8">
                  <div className="relative mx-auto w-20 h-20">
                    <div className="absolute inset-0 rounded-full border-4 border-cyan-400/30 animate-ping"></div>
                    <div className="absolute inset-2 rounded-full border-4 border-cyan-400/50 animate-pulse"></div>
                    <div className="absolute inset-4 rounded-full bg-cyan-600/20 flex items-center justify-center">
                      <Smartphone className="w-6 h-6 text-cyan-400" />
                    </div>
                  </div>
                  <p className="text-cyan-400 mt-4 font-medium">Scanning...</p>
                  <p className="text-slate-400 text-sm">Hold card near device</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={cancelOperation}
                    className="mt-4"
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <Button 
                  onClick={handleReadNFC}
                  disabled={!nfcSupported}
                  className="w-full bg-cyan-600 hover:bg-cyan-700"
                >
                  <Scan className="w-4 h-4 mr-2" />
                  Scan NFC Card
                </Button>
              )}

              {/* Read Result */}
              {lastRead && (
                <div className="bg-slate-700/50 rounded-lg p-4 space-y-3">
                  <div className="flex items-center gap-2 text-green-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="font-medium text-sm">Card Read Successfully</span>
                  </div>
                  
                  <div className="space-y-2 text-sm">
                    <div>
                      <span className="text-slate-400">Serial: </span>
                      <span className="text-white font-mono">{lastRead.serialNumber}</span>
                    </div>
                    
                    {lastRead.records.map((record, i) => (
                      <div key={i} className="bg-slate-800 rounded p-2">
                        <span className="text-slate-400 text-xs uppercase">{record.type}: </span>
                        <span className="text-cyan-400 break-all">{record.data}</span>
                      </div>
                    ))}
                    
                    <div className="text-slate-500 text-xs">
                      Read at: {lastRead.timestamp}
                    </div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Write NFC Card */}
          <Card className="bg-slate-800 border-slate-700">
            <CardHeader className="pb-2">
              <CardTitle className="text-white text-base sm:text-lg flex items-center gap-2">
                <PenTool className="w-5 h-5 text-purple-400" />
                Write Card
              </CardTitle>
              <CardDescription>
                Program a card with a member profile URL
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {isWriting ? (
                <div className="text-center py-8">
                  <div className="relative mx-auto w-20 h-20">
                    <div className="absolute inset-0 rounded-full border-4 border-purple-400/30 animate-ping"></div>
                    <div className="absolute inset-2 rounded-full border-4 border-purple-400/50 animate-pulse"></div>
                    <div className="absolute inset-4 rounded-full bg-purple-600/20 flex items-center justify-center">
                      <PenTool className="w-6 h-6 text-purple-400" />
                    </div>
                  </div>
                  <p className="text-purple-400 mt-4 font-medium">Writing...</p>
                  <p className="text-slate-400 text-sm">Hold card near device</p>
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={cancelOperation}
                    className="mt-4"
                  >
                    Cancel
                  </Button>
                </div>
              ) : (
                <>
                  {/* Write Mode Selection */}
                  <div className="flex gap-2">
                    <Button
                      variant={writeMode === 'member' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setWriteMode('member')}
                      className={writeMode === 'member' ? 'bg-purple-600' : ''}
                    >
                      <User className="w-4 h-4 mr-1" />
                      Member
                    </Button>
                    <Button
                      variant={writeMode === 'custom' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setWriteMode('custom')}
                      className={writeMode === 'custom' ? 'bg-purple-600' : ''}
                    >
                      <Link2 className="w-4 h-4 mr-1" />
                      Custom URL
                    </Button>
                  </div>

                  {writeMode === 'member' ? (
                    <div className="space-y-3">
                      <Label className="text-sm">Select Member</Label>
                      <Select value={selectedMember} onValueChange={setSelectedMember}>
                        <SelectTrigger className="bg-slate-700 border-slate-600">
                          <SelectValue placeholder="Choose a member..." />
                        </SelectTrigger>
                        <SelectContent>
                          {loadingMembers ? (
                            <SelectItem value="_loading" disabled>Loading...</SelectItem>
                          ) : members.length === 0 ? (
                            <SelectItem value="_none" disabled>No members found</SelectItem>
                          ) : (
                            members.map((member) => (
                              <SelectItem 
                                key={member._id || member.id} 
                                value={member._id || member.id}
                              >
                                {member.firstName} {member.lastName} - {member.handle || member.username || 'No handle'}
                              </SelectItem>
                            ))
                          )}
                        </SelectContent>
                      </Select>

                      {selectedMemberData && (
                        <div className="bg-slate-700/50 rounded-lg p-3 text-sm">
                          <p className="text-white font-medium">
                            {selectedMemberData.firstName} {selectedMemberData.lastName}
                          </p>
                          <p className="text-slate-400 text-xs mt-1 break-all">
                            URL: {getMemberProfileUrl(selectedMember)}
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <Label className="text-sm">Custom URL</Label>
                      <Input
                        value={customUrl}
                        onChange={(e) => setCustomUrl(e.target.value)}
                        placeholder="https://example.com/profile"
                        className="bg-slate-700 border-slate-600"
                      />
                      <p className="text-slate-500 text-xs">
                        Enter any URL to program onto the card
                      </p>
                    </div>
                  )}

                  <Button 
                    onClick={handleWriteNFC}
                    disabled={!nfcSupported || (writeMode === 'member' && !selectedMember) || (writeMode === 'custom' && !customUrl)}
                    className="w-full bg-purple-600 hover:bg-purple-700"
                  >
                    <PenTool className="w-4 h-4 mr-2" />
                    Write to Card
                  </Button>
                </>
              )}

              {/* Write Result */}
              {writeSuccess && (
                <div className="bg-slate-700/50 rounded-lg p-4 space-y-2">
                  <div className="flex items-center gap-2 text-green-400">
                    <CheckCircle2 className="w-4 h-4" />
                    <span className="font-medium text-sm">Card Written Successfully!</span>
                  </div>
                  <div className="text-sm">
                    <span className="text-slate-400">URL: </span>
                    <span className="text-purple-400 break-all">{writeSuccess.url}</span>
                  </div>
                  <div className="text-slate-500 text-xs">
                    Written at: {writeSuccess.timestamp}
                  </div>
                </div>
              )}

              {writeSuccess === false && (
                <div className="bg-red-900/20 rounded-lg p-4">
                  <div className="flex items-center gap-2 text-red-400">
                    <XCircle className="w-4 h-4" />
                    <span className="font-medium text-sm">Write Failed</span>
                  </div>
                  <p className="text-slate-400 text-xs mt-1">
                    Make sure the card is held steady near the device.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Instructions */}
        <Card className="bg-slate-800 border-slate-700">
          <CardHeader className="pb-2">
            <CardTitle className="text-white text-base">How to Use</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-600/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-blue-400 font-bold">1</span>
                </div>
                <div>
                  <p className="text-white font-medium">Select Content</p>
                  <p className="text-slate-400 text-xs">Choose a member or enter a custom URL</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-purple-600/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-purple-400 font-bold">2</span>
                </div>
                <div>
                  <p className="text-white font-medium">Tap Write</p>
                  <p className="text-slate-400 text-xs">Click the write button to start</p>
                </div>
              </div>
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-green-600/20 flex items-center justify-center flex-shrink-0">
                  <span className="text-green-400 font-bold">3</span>
                </div>
                <div>
                  <p className="text-white font-medium">Hold Card</p>
                  <p className="text-slate-400 text-xs">Place NFC card on back of phone</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tips */}
        <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
          <h4 className="text-white font-medium text-sm mb-2 flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-yellow-400" />
            Tips for Best Results
          </h4>
          <ul className="text-slate-400 text-xs space-y-1">
            <li>• Hold the card flat against the back of your phone</li>
            <li>• Keep the card still until the operation completes</li>
            <li>• NFC antenna is usually in the upper half of the phone</li>
            <li>• Remove any phone case if having trouble</li>
            <li>• NTAG215 cards support up to 504 bytes of data</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
