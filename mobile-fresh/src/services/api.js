import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL = 'https://studio-app-7y7z.onrender.com';
const SESSION_KEY = 'studio_session';

const client = axios.create({
  baseURL: BASE_URL,
  timeout: 60000,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use(async (config) => {
  const session = await AsyncStorage.getItem(SESSION_KEY);
  if (session) {
    config.headers['Authorization'] = `Bearer ${session}`;
  }
  return config;
});

export async function login(email, password) {
  const res = await client.post('/api/mobile/login', { email, password });
  if (res.data.ok) {
    await AsyncStorage.setItem(SESSION_KEY, res.data.session);
  }
  return res.data;
}

export async function logout() {
  await AsyncStorage.removeItem(SESSION_KEY);
}

export async function isLoggedIn() {
  const session = await AsyncStorage.getItem(SESSION_KEY);
  return !!session;
}

export async function getTodayLessons() {
  const res = await client.get('/api/mobile/lessons/today');
  return res.data;
}

export async function getStudents() {
  const res = await client.get('/api/mobile/students');
  return res.data;
}

export async function recordAttendance(studentName, status, eventDate, durationMinutes = 60) {
  const res = await client.post('/api/mobile/record-attendance', {
    student_name: studentName,
    status,
    event_date: eventDate,
    duration_minutes: durationMinutes,
  });
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
  const res = await client.post('/api/mobile/lesson-note', {
    student_name: studentName,
    date,
    notes,
    assignment,
  });
  return res.data;
}

export async function recordPayment(studentName, amount, method, notes = '', date) {
  const res = await client.post('/api/mobile/payment', {
    student_name: studentName,
    amount,
    method,
    notes,
    date,
  });
  return res.data;
}

export async function registerPushToken(token) {
  const res = await client.post('/api/mobile/register-push', { token });
  return res.data;
}
