import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActivityIndicator, Text, TouchableOpacity, View } from 'react-native';

import * as Notifications from 'expo-notifications';

import RoleSelectScreen      from '../screens/RoleSelectScreen';
import TeacherLoginScreen    from '../screens/LoginScreen';
import DashboardScreen       from '../screens/DashboardScreen';
import ScheduleScreen        from '../screens/ScheduleScreen';
import StudentsScreen        from '../screens/StudentsScreen';
import StudentProfileScreen  from '../screens/StudentProfileScreen';
import AttendanceScreen      from '../screens/AttendanceScreen';
import LessonNoteScreen      from '../screens/LessonNoteScreen';
import TeacherPaymentScreen  from '../screens/PaymentScreen';
import OnboardingScreen      from '../screens/OnboardingScreen';
import StripeConnectScreen   from '../screens/StripeConnectScreen';
import MoreScreen            from '../screens/MoreScreen';

import ParentLoginScreen     from '../screens/parent/LoginScreen';
import ParentDashboard       from '../screens/parent/DashboardScreen';
import ParentNotes           from '../screens/parent/NotesScreen';
import ParentPayment         from '../screens/parent/PaymentScreen';

import StudentLoginScreen    from '../screens/student/LoginScreen';
import StudentDashboard      from '../screens/student/DashboardScreen';
import StudentNotes          from '../screens/student/NotesScreen';

import { isLoggedIn, logout, getStoredRole, registerPushToken } from '../services/api';
import { COLORS } from '../theme';

const Stack = createNativeStackNavigator();
const Tab   = createBottomTabNavigator();


Notifications.setNotificationHandler({ handleNotification: async () => ({ shouldShowAlert: true, shouldPlaySound: true, shouldSetBadge: false }) });

const TAB_BAR_STYLE = {
  backgroundColor: '#fff',
  borderTopColor: COLORS.border,
  borderTopWidth: 1,
  height: 82,
  paddingTop: 8,
  paddingBottom: 16,
};
const TAB_LABEL_STYLE = { fontSize: 11, fontWeight: '600', marginTop: 2 };
const HEADER_STYLE = { backgroundColor: '#fff', borderBottomWidth: 0, elevation: 0, shadowOpacity: 0 };

function TeacherTabs({ navigation }) {
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      tabBarIcon: ({ focused }) => {
        const icons = { Today: '📅', Schedule: '🗓️', Students: '👥', Payments: '💳', More: '⋯' };
        return <Text style={{ fontSize: focused ? 22 : 19, opacity: focused ? 1 : 0.5 }}>{icons[route.name]}</Text>;
      },
      tabBarActiveTintColor: COLORS.primary, tabBarInactiveTintColor: COLORS.muted,
      tabBarLabelStyle: TAB_LABEL_STYLE,
      tabBarStyle: TAB_BAR_STYLE,
      headerStyle: HEADER_STYLE,
      headerTitleStyle: { color: COLORS.text, fontWeight: '800', fontSize: 19 },
      headerTintColor: COLORS.text,
    })}>
      <Tab.Screen name="Today"    component={DashboardScreen}      options={{ title: "Today's Lessons" }} />
      <Tab.Screen name="Schedule" component={ScheduleScreen}       options={{ title: 'Schedule' }} />
      <Tab.Screen name="Students" component={StudentsScreen}       options={{ title: 'Students' }} />
      <Tab.Screen name="Payments" component={TeacherPaymentScreen} options={{ title: 'Payments' }} />
      <Tab.Screen name="More"     component={MoreScreen}           options={{ title: 'More' }} />
    </Tab.Navigator>
  );
}

function ParentTabs({ navigation }) {
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      tabBarIcon: ({ focused }) => {
        const icons = { Home: '🏠', Notes: '📝', Pay: '💳' };
        return <Text style={{ fontSize: focused ? 22 : 19, opacity: focused ? 1 : 0.5 }}>{icons[route.name]}</Text>;
      },
      tabBarActiveTintColor: '#667eea', tabBarInactiveTintColor: COLORS.muted,
      tabBarLabelStyle: TAB_LABEL_STYLE,
      tabBarStyle: TAB_BAR_STYLE,
      headerStyle: HEADER_STYLE,
      headerTitleStyle: { color: COLORS.text, fontWeight: '800', fontSize: 19 },
      headerTintColor: COLORS.text,
    })}>
      <Tab.Screen name="Home"  component={ParentDashboard} options={{ title: 'Dashboard', headerRight: () => (
        <TouchableOpacity onPress={async () => { await logout(); navigation.replace('RoleSelect'); }} style={{ marginRight: 16 }}>
          <Text style={{ color: '#667eea', fontWeight: '600', fontSize: 15 }}>Logout</Text>
        </TouchableOpacity>
      )}} />
      <Tab.Screen name="Notes" component={ParentNotes}   options={{ title: 'Lesson Notes' }} />
      <Tab.Screen name="Pay"   component={ParentPayment} options={{ title: 'Payments' }} />
    </Tab.Navigator>
  );
}

function StudentTabs({ navigation }) {
  return (
    <Tab.Navigator screenOptions={({ route }) => ({
      tabBarIcon: ({ focused }) => {
        const icons = { Home: '🏠', Notes: '📝' };
        return <Text style={{ fontSize: focused ? 22 : 19, opacity: focused ? 1 : 0.5 }}>{icons[route.name]}</Text>;
      },
      tabBarActiveTintColor: '#48bb78', tabBarInactiveTintColor: COLORS.muted,
      tabBarLabelStyle: TAB_LABEL_STYLE,
      tabBarStyle: TAB_BAR_STYLE,
      headerStyle: HEADER_STYLE,
      headerTitleStyle: { color: COLORS.text, fontWeight: '800', fontSize: 19 },
      headerTintColor: COLORS.text,
    })}>
      <Tab.Screen name="Home"  component={StudentDashboard} options={{ title: 'My Lessons', headerRight: () => (
        <TouchableOpacity onPress={async () => { await logout(); navigation.replace('RoleSelect'); }} style={{ marginRight: 16 }}>
          <Text style={{ color: '#48bb78', fontWeight: '600', fontSize: 15 }}>Logout</Text>
        </TouchableOpacity>
      )}} />
      <Tab.Screen name="Notes" component={StudentNotes} options={{ title: 'My Notes' }} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  const [checking,     setChecking]     = useState(true);
  const [initialRoute, setInitialRoute] = useState('RoleSelect');
  const [role,         setRole]         = useState(null);

  useEffect(() => {
    (async () => {
      const storedRole = await getStoredRole();
      const authed     = await isLoggedIn();
      setRole(storedRole);
      setInitialRoute(authed && storedRole ? 'Main' : storedRole ? 'Login' : 'RoleSelect');
      setChecking(false);

      if (storedRole === 'teacher') {
        try {
          const { status } = await Notifications.requestPermissionsAsync();
          if (status === 'granted') {
            const token = (await Notifications.getExpoPushTokenAsync()).data;
            await registerPushToken(token);
          }
        } catch {}
      }
    })();
  }, []);

  if (checking) {
    return <View style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: COLORS.bg }}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName={initialRoute} screenOptions={{ headerShown: false }}>
        <Stack.Screen name="RoleSelect" component={RoleSelectScreen} />

        <Stack.Screen name="Login" children={(props) => {
          const r = props.route?.params?.role || role;
          if (r === 'parent')  return <ParentLoginScreen  {...props} />;
          if (r === 'student') return <StudentLoginScreen {...props} />;
          return <TeacherLoginScreen {...props} />;
        }} />

        <Stack.Screen name="Main" children={(props) => {
          if (role === 'parent')  return <ParentTabs  {...props} />;
          if (role === 'student') return <StudentTabs {...props} />;
          return <TeacherTabs {...props} />;
        }} />

        <Stack.Screen name="Onboarding"     component={OnboardingScreen}     options={{ gestureEnabled: false }} />
        <Stack.Screen name="StudentProfile" component={StudentProfileScreen} options={{ headerShown: true, title: '' }} />
        <Stack.Screen name="Attendance"     component={AttendanceScreen}     options={{ headerShown: true, title: 'Record Attendance' }} />
        <Stack.Screen name="LessonNote"     component={LessonNoteScreen}     options={{ headerShown: true, title: 'Lesson Note' }} />
        <Stack.Screen name="StripeConnect"  component={StripeConnectScreen}  options={{ headerShown: true, title: 'Accept Payments' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
