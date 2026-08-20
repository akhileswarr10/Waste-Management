import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://dcmgdepxdjmxrptksodb.supabase.co';
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRjbWdkZXB4ZGpteHJwdGtzb2RiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcyMjcxMjUsImV4cCI6MjEwMjgwMzEyNX0.M006VW3dhG_LN9hdFeiBVMuGNoI7msy0mvTHVqK95zk';

export const supabase = createClient(supabaseUrl, supabaseKey);
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000';
