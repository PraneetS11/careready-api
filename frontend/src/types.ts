export type Role = "requester" | "provider" | "agency";
export type Profile = {
  name: string;
  agency_id: string | null;
  experience: number;
  gender: string;
  services: string[];
  languages: string[];
  approved: boolean;
  user_id: string;
};
export type Account = {
  id: string;
  email: string;
  role: Role;
  is_verified: boolean;
  profile: Profile | null;
};
export type Agency = { id: string; name: string; city: string };
export type Catalog = {
  services: Record<string, string>;
  cities: Record<
    string,
    { latitude: number; longitude: number; timezone: string }
  >;
  experience_levels: string[];
  languages: string[];
};
export type Visit = {
  id: string;
  series_id: string;
  agency_id: string;
  service: string;
  city: string;
  latitude: number;
  longitude: number;
  starts_at: string;
  duration_minutes: number;
  min_experience: number;
  gender_preference: string;
  preferred_language: string;
  communication: string;
  smoke_free: boolean;
  pets_present: boolean;
  status: string;
  recipient?: string;
  address?: string;
  notes?: string;
  provider_id: string | null;
  preference_match: boolean;
  language_match: boolean;
  timezone: string;
};
export type TeamMember = Profile & { email: string; is_verified: boolean };
export type Device = {
  id: string;
  name: string;
  asset_code: string;
  status: "available" | "in_use" | "maintenance";
};
