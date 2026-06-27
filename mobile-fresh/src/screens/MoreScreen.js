import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert } from 'react-native';
import { COLORS, SHADOW_CARD } from '../theme';
import { logout } from '../services/api';

const ITEMS = [
  { label: 'Onboarding / Setup',  icon: '🚀', screen: 'Onboarding' },
  { label: 'Stripe Payments',     icon: '💳', screen: 'StripeConnect' },
];

export default function MoreScreen({ navigation }) {
  async function handleLogout() {
    Alert.alert('Log out', 'Are you sure?', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Log out', style: 'destructive',
        onPress: async () => { await logout(); navigation.replace('RoleSelect'); },
      },
    ]);
  }

  return (
    <ScrollView style={styles.root} contentContainerStyle={{ padding: 20, paddingBottom: 40 }}>
      <Text style={styles.section}>App</Text>
      {ITEMS.map(item => (
        <TouchableOpacity
          key={item.screen}
          style={styles.row}
          onPress={() => navigation.navigate(item.screen)}
          activeOpacity={0.75}
        >
          <View style={styles.rowLeft}>
            <Text style={styles.rowIcon}>{item.icon}</Text>
            <Text style={styles.rowLabel}>{item.label}</Text>
          </View>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      ))}

      <Text style={[styles.section, { marginTop: 28 }]}>Account</Text>
      <TouchableOpacity style={[styles.row, styles.rowDanger]} onPress={handleLogout} activeOpacity={0.75}>
        <View style={styles.rowLeft}>
          <Text style={styles.rowIcon}>🚪</Text>
          <Text style={[styles.rowLabel, { color: COLORS.danger }]}>Log out</Text>
        </View>
        <Text style={[styles.chevron, { color: COLORS.danger }]}>›</Text>
      </TouchableOpacity>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:      { flex: 1, backgroundColor: COLORS.bg },
  section:   { fontSize: 11, fontWeight: '700', color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 10 },
  row:       { backgroundColor: '#fff', borderRadius: 14, padding: 16, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, borderWidth: 1, borderColor: COLORS.border, ...SHADOW_CARD },
  rowDanger: { borderColor: '#fca5a5' },
  rowLeft:   { flexDirection: 'row', alignItems: 'center', gap: 14 },
  rowIcon:   { fontSize: 22 },
  rowLabel:  { fontSize: 16, fontWeight: '600', color: COLORS.text },
  chevron:   { fontSize: 22, color: COLORS.muted, fontWeight: '300' },
});
