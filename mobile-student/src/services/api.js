import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

const BASE_URL    = 'https://studio-app-7y7z.onrender.com';
const SESSION_KEY = 'student_session';
const NAME_KEY    = 'student_name';

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

export async function login(studentName, accessCode) {
  const res = await client.post('/api/mobile/student/login', { student_name: studentName, access_code: accessCode });
  if (res.data.ok) {
    await AsyncStorage.setItem(SESSION_KEY, res.data.session);
    await AsyncStorage.setItem(NAME_KEY, res.data.student_name);
  }
  return res.data;
}

export async function logout() {
  await AsyncStorage.removeItem(SESSION_KEY);
  await AsyncStorage.removeItem(NAME_KEY);
}

export async function isLoggedIn() {
  const session = await AsyncStorage.getItem(SESSION_KEY);
  return !!session;
}

export async function getStudentName() {
  return await AsyncStorage.getItem(NAME_KEY) || '';
}

export async function getDashboard() {
  const res = await client.get('/api/mobile/student/dashboard');
  return res.data;
}
