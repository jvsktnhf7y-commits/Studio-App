import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { ActivityIndicator, Text, TouchableOpacity, View, Modal, StyleSheet } from 'react-native';

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
import SettingsScreen        from '../screens/SettingsScreen';
import AdminScreen           from '../screens/AdminScreen';

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

const MORE_ITEMS = [
  { label: 'Settings',           icon: '⚙️',  screen: 'Settings' },
  { label: 'Admin & Stats',      icon: '🔐', screen: 'Admin' },
  { label: 'Onboarding / Setup', icon: '🚀', screen: 'Onboarding' },
  { label: 'Stripe Payments',    icon: '💳', screen: 'StripeConnect' },
];

function MorePlaceholder() { return <View style={{ flex: 1, backgroundColor: COLORS.bg }} />; }

function TeacherTabs({ navigation }) {
  const [showMore, setShowMore] = useState(false);

  return (
    <>
      <Tab.Navigator screenOptions={({ route }) => ({
        tabBarIcon: ({ focused }) => {
          const icons = { Today: '📅', Schedule: '🗓️', Students: '👥', Payments: '💳', More: '⋯' };
          return <Text style={{ fontSize: focused ? 22 : 20, opacity: focused ? 1 : 0.5 }}>{icons[route.name]}</Text>;
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
        <Tab.Screen
          name="More"
          component={MorePlaceholder}
          options={{ title: 'More' }}
          listeners={{ tabPress: e => { e.preventDefault(); setShowMore(true); } }}
        />
      </Tab.Navigator>

      <Modal visible={showMore} transparent animationType="fade" onRequestClose={() => setShowMore(false)}>
        <TouchableOpacity style={moreStyles.backdrop} activeOpacity={1} onPress={() => setShowMore(false)} />
        <View style={moreStyles.sheet}>
          {MORE_ITEMS.map(item => (
            <TouchableOpacity
              key={item.screen}
              style={moreStyles.item}
              onPress={() => { setShowMore(false); navigation.navigate(item.screen); }}
            >
              <Text style={moreStyles.itemIcon}>{item.icon}</Text>
              <Text style={moreStyles.itemLabel}>{item.label}</Text>
              <Text style={moreStyles.chevron}>›</Text>
            </TouchableOpacity>
          ))}
          <View style={moreStyles.divider} />
          <TouchableOpacity
            style={moreStyles.item}
            onPress={async () => { setShowMore(false); await logout(); navigation.replace('RoleSelect'); }}
          >
            <Text style={moreStyles.itemIcon}>🚪</Text>
            <Text style={[moreStyles.itemLabel, { color: COLORS.danger }]}>Log out</Text>
            <Text style={[moreStyles.chevron, { color: COLORS.danger }]}>›</Text>
          </TouchableOpacity>
        </View>
      </Modal>
    </>
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

        <Stack.Screen name="Settings"        component={SettingsScreen}       options={{ headerShown: true, title: 'Settings' }} />
        <Stack.Screen name="Admin"           component={AdminScreen}          options={{ headerShown: true, title: 'Admin' }} />
        <Stack.Screen name="Onboarding"     component={OnboardingScreen}     options={{ gestureEnabled: false }} />
        <Stack.Screen name="StudentProfile" component={StudentProfileScreen} options={{ headerShown: true, title: '' }} />
        <Stack.Screen name="Attendance"     component={AttendanceScreen}     options={{ headerShown: true, title: 'Record Attendance' }} />
        <Stack.Screen name="LessonNote"     component={LessonNoteScreen}     options={{ headerShown: true, title: 'Lesson Note' }} />
        <Stack.Screen name="StripeConnect"  component={StripeConnectScreen}  options={{ headerShown: true, title: 'Accept Payments' }} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const moreStyles = StyleSheet.create({
  backdrop:  { flex: 1, backgroundColor: 'rgba(0,0,0,0.4)' },
  sheet:     { backgroundColor: '#fff', borderTopLeftRadius: 20, borderTopRightRadius: 20, paddingVertical: 12, paddingHorizontal: 8, paddingBottom: 36 },
  item:      { flexDirection: 'row', alignItems: 'center', gap: 14, padding: 16, borderRadius: 12 },
  itemIcon:  { fontSize: 22, width: 28, textAlign: 'center' },
  itemLabel: { flex: 1, fontSize: 16, fontWeight: '600', color: '#18181b' },
  chevron:   { fontSize: 22, color: '#a1a1aa' },
  divider:   { height: 1, backgroundColor: '#e4e4e7', marginVertical: 6, marginHorizontal: 8 },
});
