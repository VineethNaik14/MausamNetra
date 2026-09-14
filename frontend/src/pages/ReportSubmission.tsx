import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { reportsApi, sourcesApi } from '../services/api';
import { MapPin, UploadCloud, AlertCircle, ArrowLeft, Clock } from 'lucide-react';

// Matches ml/classification's trained model classes exactly (see
// ml/classification/models/metadata_event-classifier-v1.json), which is
// what RealEventClassifier actually sends the backend — not the
// MockEventClassifier's keyword list. The backend upper-cases these
// before storing them as event_type_hint.
const EVENT_TYPES = [
  { value: '', label: 'Not sure — let AI decide' },
  { value: 'flood', label: 'Flood' },
  { value: 'heavy_rainfall', label: 'Heavy Rainfall' },
  { value: 'thunderstorm', label: 'Thunderstorm' },
  { value: 'heatwave', label: 'Heatwave' },
  { value: 'fog', label: 'Fog' },
  { value: 'dust_storm', label: 'Dust Storm' },
  { value: 'strong_wind', label: 'Strong Wind' },
  { value: 'cyclone', label: 'Cyclone' },
  { value: 'lightning', label: 'Lightning' },
  { value: 'hailstorm', label: 'Hailstorm' },
  { value: 'other', label: 'Other' },
];

export default function ReportSubmission() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sourceId, setSourceId] = useState<string | null>(null);
  const [mediaUrl, setMediaUrl] = useState<string | null>(null);
  const [mediaFileName, setMediaFileName] = useState<string | null>(null);

  const [formData, setFormData] = useState({
    description: '',
    lat: '',
    lng: '',
    occurredAt: '',
    eventType: '',
  });

  // The backend classifies event_type itself from the report text - it
  // doesn't take one on submission. We just need a valid source_id
  // (the "citizen" source, seeded by scripts/seed.py) to submit at all.
  useEffect(() => {
    sourcesApi
      .getSources()
      .then(({ data }) => {
        const citizenSource = data.find((s) => s.type === 'citizen' && s.is_active) || data.find((s) => s.is_active);
        if (citizenSource) {
          setSourceId(citizenSource.id);
        } else {
          setError('No active report source is configured on the server.');
        }
      })
      .catch(() => setError('Could not reach the server to load report sources.'));
  }, []);

  const handleLocation = () => {
    if ('geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setFormData(prev => ({
            ...prev,
            lat: pos.coords.latitude.toString(),
            lng: pos.coords.longitude.toString()
          }));
        },
        () => setError('Location access denied. Please enter manually.')
      );
    }
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const res = await reportsApi.uploadMedia(file);
      setMediaUrl(res.data.media_url);
      setMediaFileName(file.name);
    } catch (err) {
      setError('Failed to upload file.');
    } finally {
      setUploading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceId) {
      setError('Report source is not ready yet - please wait a moment and try again.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await reportsApi.submitReport({
        source_id: sourceId,
        text: formData.description,
        latitude: parseFloat(formData.lat) || 0,
        longitude: parseFloat(formData.lng) || 0,
        media_url: mediaUrl || undefined,
        timestamp: formData.occurredAt ? new Date(formData.occurredAt).toISOString() : undefined,
        event_type_hint: formData.eventType ? formData.eventType.toUpperCase() : undefined,
      });
      navigate('/', { replace: true });
    } catch (err) {
      setError('Failed to submit report.');
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-4">
        <button
          onClick={() => navigate(-1)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-[#24313D] border border-[#34C759]/30 rounded-md text-[#34C759] text-sm font-medium hover:bg-[#34C759] hover:text-[#1C2833] hover:border-[#34C759] transition-colors mb-6 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759] focus-visible:ring-offset-2 focus-visible:ring-offset-[#1C2833]"
        >
          <ArrowLeft className="h-4 w-4" /> Back
        </button>
      </div>
      <div className="bg-[#24313D] rounded-xl shadow-sm border border-[#34C759]/20 p-6 md:p-8">
        <h1 className="text-2xl font-bold text-[#F4F6F6] mb-2">Report an Incident</h1>
        <p className="text-sm text-[#34C759]/70 mb-8">Your report helps us monitor and verify weather events in real-time. Our AI will automatically classify the event type from your description.</p>

        {error && (
          <div className="mb-6 p-4 bg-red-900/30 text-red-400 border border-red-900/50 rounded-md flex items-center gap-2 text-sm">
            <AlertCircle className="h-5 w-5" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label className="block text-sm font-medium text-[#34C759]/90 mb-1">Description</label>
            <textarea
              required
              rows={4}
              placeholder="Describe the situation (e.g. 'Heavy flooding on MG Road, water knee-deep')..."
              value={formData.description}
              onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
              className="w-full px-4 py-2 bg-[#24313D] border border-[#34C759]/40 text-[#F4F6F6] rounded-md focus:ring-[#34C759] focus:border-[#34C759]/40 resize-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#34C759]/90 mb-1">Event Type (optional)</label>
            <select
              value={formData.eventType}
              onChange={(e) => setFormData(prev => ({ ...prev, eventType: e.target.value }))}
              className="w-full px-4 py-2 bg-[#24313D] border border-[#34C759]/40 text-[#F4F6F6] rounded-md focus:ring-[#34C759] focus:border-[#34C759]/40"
            >
              {EVENT_TYPES.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
            <p className="text-xs text-[#34C759]/60 mt-1">Leave as "Not sure" and our AI will classify it from your description.</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#34C759]/90 mb-1">When did this happen? (optional)</label>
            <input
              type="datetime-local"
              value={formData.occurredAt}
              max={new Date().toISOString().slice(0, 16)}
              onChange={(e) => setFormData(prev => ({ ...prev, occurredAt: e.target.value }))}
              className="w-full px-4 py-2 bg-[#24313D] border border-[#34C759]/40 text-[#F4F6F6] rounded-md focus:ring-[#34C759] focus:border-[#34C759]/40"
            />
            <p className="text-xs text-[#34C759]/60 mt-1">Leave blank to use the current time.</p>
          </div>
          <div>
            <label className="block text-sm font-medium text-[#34C759]/90 mb-1">Location (GPS)</label>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                placeholder="Latitude"
                required
                value={formData.lat}
                onChange={(e) => setFormData(prev => ({ ...prev, lat: e.target.value }))}
                className="w-full px-4 py-2 bg-[#24313D] border border-[#34C759]/40 text-[#F4F6F6] rounded-md focus:ring-[#34C759] focus:border-[#34C759]/40"
              />
              <input
                type="text"
                placeholder="Longitude"
                required
                value={formData.lng}
                onChange={(e) => setFormData(prev => ({ ...prev, lng: e.target.value }))}
                className="w-full px-4 py-2 bg-[#24313D] border border-[#34C759]/40 text-[#F4F6F6] rounded-md focus:ring-[#34C759] focus:border-[#34C759]/40"
              />
            </div>
            <button
              type="button"
              onClick={handleLocation}
              className="inline-flex items-center gap-2 text-sm text-[#34C759]/90 hover:text-[#db4918] font-medium transition-colors"
            >
              <MapPin className="h-4 w-4" /> Get Current Location
            </button>
          </div>

          <div>
            <label className="block text-sm font-medium text-[#34C759]/90 mb-1">Photo/Video Upload</label>
            <label className="border-2 border-dashed border-[#34C759]/40 rounded-lg p-8 flex flex-col items-center justify-center text-center hover:bg-[#24313D] transition-colors cursor-pointer bg-[#1C2833]/80 block">
              <input type="file" accept="image/jpeg,image/png,image/webp,video/mp4,video/quicktime,video/webm" className="hidden" onChange={handleFileChange} />
              <UploadCloud className="h-8 w-8 text-[#34C759] mb-2" />
              <p className="text-sm font-medium text-[#34C759]/90">
                {uploading ? 'Uploading...' : mediaFileName ? `Selected: ${mediaFileName}` : 'Click to upload or drag and drop'}
              </p>
              <p className="text-xs text-[#34C759] mt-1">JPG, PNG, WEBP, MP4, MOV or WEBM (max. 10MB)</p>
            </label>
          </div>

          <div className="pt-4 border-t border-[#34C759]/20">
            <button
              type="submit"
              disabled={loading || uploading}
              className="w-full bg-[#34C759] text-[#1C2833] font-semibold py-3 px-4 rounded-md hover:bg-[#E8C15A] hover:text-[#1C2833]/80 transition-colors disabled:bg-[#1C2833]/80 disabled:cursor-not-allowed"
            >
              {loading ? 'Submitting...' : 'Submit Report'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
