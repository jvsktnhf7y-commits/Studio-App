import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActivityIndicator, Text, TouchableOpacity, View, Platform } from 'react-native';
import * as Notifications from 'expo-notifications';

import LoginScreen           from '../screens/LoginScreen';
import OnboardingScreen      from '../screens/OnboardingScreen';
import StripeConnectScreen   from '../screens/StripeConnectScreen';
import DashboardScreen      from '../screens/DashboardScreen';
import ScheduleScreen       from '../screens/ScheduleScreen';
import StudentsScreen       from '../screens/StudentsScreen';
import AttendanceScreen     from '../screens/AttendanceScreen';
import StudentProfileScreen from '../screens/StudentProfileScreen';
import LessonNoteScreen     from '../screens/LessonNoteScreen';
import PaymentScreen        from '../screens/PaymentScreen';
import { isLoggedIn, logout, registerPushToken } from '../services/api';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { COLORS, GRADIENT } from '../theme';

const Stack = createNativeStackNavigator();
const Tab   = createBottomTabNavigator();

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge:  false,
  }),
});

async function registerForPushNotifications() {
  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    if (finalStatus !== 'granted') return;
    const token = (await Notifications.getExpoPushTokenAsync()).data;
    await registerPushToken(token);
  } catch {
    // Notifications are optional — don't block the app
  }
}

function TabIcon({ label, focused }) {
  const icons = { Today: '📅', Schedule: '🗓️', Students: '👥', Payments: '💳' };
  return (
    <Text style={{ fontSize: focused ? 22 : 19, opacity: focused ? 1 : 0.5 }}>
      {icons[label]}
    </Text>
  );
}

function MainTabs({ navigation }) {
  async function handleLogout() {
    await logout();
    navigation.replace('Login');
  }

  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused }) => <TabIcon label={route.name} focused={focused} />,
        tabBarActiveTintColor:   COLORS.primary,
        tabBarInactiveTintColor: COLORS.muted,
        tabBarLabelStyle:  { fontSize: 12, fontWeight: '600', marginBottom: 4 },
        tabBarStyle: {
          backgroundColor: '#fff',
          borderTopColor:  COLORS.border,
          borderTopWidth:  1,
          height: 62,
          paddingTop: 6,
        },
        headerStyle:       { backgroundColor: '#fff', borderBottomWidth: 0, elevation: 0, shadowOpacity: 0 },
        headerTitleStyle:  { color: COLORS.text, fontWeight: '800', fontSize: 19 },
        headerTintColor:   COLORS.text,
      })}
    >
      <Tab.Screen
        name="Today"
        component={DashboardScreen}
        options={{
          title: "Today's Lessons",
          headerRight: () => (
            <TouchableOpacity onPress={handleLogout} style={{ marginRight: 16 }}>
              <Text style={{ color: COLORS.primary, fontWeight: '600', fontSize: 15 }}>Logout</Text>
            </TouchableOpacity>
          ),
        }}
      />
      <Tab.Screen
        name="Schedule"
        component={ScheduleScreen}
        options={{ title: 'Schedule' }}
      />
      <Tab.Screen
        name="Students"
        component={StudentsScreen}
        options={{ title: 'Students' }}
      />
      <Tab.Screen
        name="Payments"
        component={StripeConnectScreen}
        options={{ title: 'Payments' }}
      />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const [checking,    setChecking]    = useState(true);
  const [authed,      setAuthed]      = useState(false);
  const [onboarded,   setOnboarded]   = useState(true);

  useEffect(() => {
    Promise.all([isLoggedIn(), AsyncStorage.getItem('onboarding_done')]).then(([loggedIn, done]) => {
      setAuthed(loggedIn);
      setOnboarded(!!done);
      setChecking(false);
      if (loggedIn) registerForPushNotifications();
    });
  }, []);

  if (checking) {
    return (
      <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.bg }}>
        <ActivityIndicator size="large" color={COLORS.primary} />
      </View>
    );
  }

  const sharedHeaderOptions = {
    headerShown:      true,
    headerStyle:      { backgroundColor: '#fff', elevation: 0, shadowOpacity: 0 },
    headerTitleStyle: { color: COLORS.text, fontWeight: '800', fontSize: 18 },
    headerTintColor:  COLORS.primary,
  };

  return (
    <NavigationContainer>
      <Stack.Navigator
        initialRouteName={authed ? 'Main' : onboarded ? 'Login' : 'Onboarding'}
        screenOptions={{ headerShown: false }}
      >
        <Stack.Screen name="Onboarding" component={OnboardingScreen} />
        <Stack.Screen name="Login"      component={LoginScreen} />
        <Stack.Screen name="Main"  component={MainTabs} />
        <Stack.Screen name="Attendance"     component={AttendanceScreen}     options={{ ...sharedHeaderOptions, title: 'Record Attendance' }} />
        <Stack.Screen name="StudentProfile" component={StudentProfileScreen} options={{ ...sharedHeaderOptions, title: '' }} />
        <Stack.Screen name="LessonNote"     component={LessonNoteScreen}     options={{ ...sharedHeaderOptions, title: 'Lesson Note' }} />
        <Stack.Screen name="Payment"        component={PaymentScreen}        options={{ ...sharedHeaderOptions, title: 'Record Payment' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
