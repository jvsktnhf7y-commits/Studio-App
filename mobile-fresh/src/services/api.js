import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL    = 'https://studio-app-7y7z.onrender.com';
const SESSION_KEY = 'studio_session';
const PARENT_KEY  = 'parent_session';
const STUDENT_KEY = 'student_session';

// ── Teacher client ────────────────────────────────────────────────────────────
const client = axios.create({ baseURL: BASE_URL, timeout: 60000, headers: { 'Content-Type': 'application/json' } });
client.interceptors.request.use(async (config) => {
  const session = await AsyncStorage.getItem(SESSION_KEY);
  if (session) config.headers['Authorization'] = `Bearer ${session}`;
  return config;
});

// ── Parent client ─────────────────────────────────────────────────────────────
const parentClient = axios.create({ baseURL: BASE_URL, timeout: 60000, headers: { 'Content-Type': 'application/json' } });
parentClient.interceptors.request.use(async (config) => {
  const session = await AsyncStorage.getItem(PARENT_KEY);
  if (session) config.headers['Authorization'] = `Bearer parent:${session}`;
  return config;
});

// ── Student client ────────────────────────────────────────────────────────────
const studentClient = axios.create({ baseURL: BASE_URL, timeout: 60000, headers: { 'Content-Type': 'application/json' } });
studentClient.interceptors.request.use(async (config) => {
  const session = await AsyncStorage.getItem(STUDENT_KEY);
  if (session) config.headers['Authorization'] = `Bearer student:${session}`;
  return config;
});

// ── Role detection ────────────────────────────────────────────────────────────
export async function getStoredRole() {
  return AsyncStorage.getItem('app_role');
}

export async function isLoggedIn() {
  const role = await getStoredRole();
  if (role === 'parent')  return !!(await AsyncStorage.getItem(PARENT_KEY));
  if (role === 'student') return !!(await AsyncStorage.getItem(STUDENT_KEY));
  return !!(await AsyncStorage.getItem(SESSION_KEY));
}

export async function logout() {
  const role = await getStoredRole();
  if (role === 'parent')  await AsyncStorage.removeItem(PARENT_KEY);
  else if (role === 'student') await AsyncStorage.removeItem(STUDENT_KEY);
  else await AsyncStorage.removeItem(SESSION_KEY);
  await AsyncStorage.removeItem('app_role');
}

// ── Teacher auth ──────────────────────────────────────────────────────────────
export async function login(email, password) {
  const res = await client.post('/api/mobile/login', { email, password });
  if (res.data.ok) await AsyncStorage.setItem(SESSION_KEY, res.data.session);
  return res.data;
}

// ── Parent auth ───────────────────────────────────────────────────────────────
export async function parentLogin(studentName, parentCode) {
  const res = await axios.post(`${BASE_URL}/api/mobile/parent/login`, { student_name: studentName, parent_code: parentCode });
  if (res.data.ok) await AsyncStorage.setItem(PARENT_KEY, res.data.session);
  return res.data;
}

// ── Student auth ──────────────────────────────────────────────────────────────
export async function studentLogin(studentName, accessCode) {
  const res = await axios.post(`${BASE_URL}/api/mobile/student/login`, { student_name: studentName, access_code: accessCode });
  if (res.data.ok) await AsyncStorage.setItem(STUDENT_KEY, res.data.session);
  return res.data;
}

// ── Teacher API ───────────────────────────────────────────────────────────────
export async function getTodayLessons() {
  const res = await client.get('/api/mobile/lessons/today');
  return res.data;
}
export async function getStudents() {
  const res = await client.get('/api/mobile/students');
  return res.data;
}
export async function recordAttendance(studentName, status, eventDate, durationMinutes = 60) {
  const res = await client.post('/api/mobile/record-attendance', { student_name: studentName, status, event_date: eventDate, duration_minutes: durationMinutes });
  return res.data;
}
export async function getSchedule() {
  const res = await client.get('/api/mobile/schedule');
  return res.data;
}
export async function getStudentProfile(name) {
  const res = await client.get(`/api/mobile/student/${encodeURIComponent(name)}`);
  return res.data;
}
export async function saveLessonNote(studentName, date, notes, assignment = '') {
  const res = await client.post('/api/mobile/lesson-note', { student_name: studentName, date, notes, assignment });
  return res.data;
}
export async function recordPayment(studentName, amount, method, notes = '', date) {
  const res = await client.post('/api/mobile/payment', { student_name: studentName, amount, method, notes, date });
  return res.data;
}
export async function registerPushToken(token) {
  const res = await client.post('/api/mobile/register-push', { token });
  return res.data;
}
export async function setAccessCode(studentName, code) {
  const res = await client.post(`/api/mobile/student/${encodeURIComponent(studentName)}/access-code`, { code });
  return res.data;
}
export async function setParentCode(studentName, code) {
  const res = await client.post(`/api/mobile/student/${encodeURIComponent(studentName)}/parent-code`, { code });
  return res.data;
}

// ── Parent API ────────────────────────────────────────────────────────────────
export async function parentGetDashboard() {
  const res = await parentClient.get('/api/mobile/parent/dashboard');
  return res.data;
}
export async function parentGetNotes() {
  const res = await parentClient.get('/api/mobile/parent/notes');
  return res.data;
}
export async function parentCreatePaymentIntent(amountCents, description) {
  const res = await parentClient.post('/api/mobile/parent/create-payment-intent', { amount_cents: amountCents, description });
  return res.data;
}

// ── Student API ───────────────────────────────────────────────────────────────
export async function studentGetDashboard() {
  const res = await studentClient.get('/api/mobile/student/dashboard');
  return res.data;
}
