import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView,
  ActivityIndicator, Alert, TouchableOpacity, Linking,
} from 'react-native';
import { getAdminStats } from '../services/api';
import { COLORS, SHADOW_CARD } from '../theme';

const BASE_URL = 'https://studio-app-7y7z.onrender.com';

export default function AdminScreen() {
  const [loading, setLoading] = useState(true);
  const [stats,   setStats]   = useState(null);

  useEffect(() => {
    getAdminStats()
      .then(d => { if (d.ok) setStats(d); })
      .catch(() => Alert.alert('Error', 'Could not load stats.'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;
  }

  return (
    <ScrollView style={styles.root} contentContainerStyle={styles.body}>
      <Text style={styles.sectionLabel}>Overview</Text>
      <View style={styles.statsRow}>
        <View style={styles.statCard}>
          <Text style={styles.statIcon}>👥</Text>
          <Text style={styles.statVal}>{stats?.student_count ?? '—'}</Text>
          <Text style={styles.statLbl}>Students</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statIcon}>💵</Text>
          <Text style={styles.statVal}>${stats?.total_revenue?.toFixed(2) ?? '—'}</Text>
          <Text style={styles.statLbl}>Total Revenue</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statIcon}>💳</Text>
          <Text style={styles.statVal}>${stats?.total_prepaid?.toFixed(2) ?? '—'}</Text>
          <Text style={styles.statLbl}>Prepaid</Text>
        </View>
      </View>

      <Text style={[styles.sectionLabel, { marginTop: 20 }]}>Data Backup</Text>
      <View style={styles.card}>
        <TouchableOpacity style={styles.linkBtn} onPress={() => Linking.openURL(`${BASE_URL}/api/backup`)}>
          <Text style={styles.linkBtnIcon}>📥</Text>
          <Text style={styles.linkBtnText}>Download JSON Backup</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
        <View style={styles.divider} />
        <TouchableOpacity style={styles.linkBtn} onPress={() => Linking.openURL(`${BASE_URL}/api/backup/csv`)}>
          <Text style={styles.linkBtnIcon}>📦</Text>
          <Text style={styles.linkBtnText}>Download CSV Backup (ZIP)</Text>
          <Text style={styles.chevron}>›</Text>
        </TouchableOpacity>
      </View>

      <Text style={[styles.sectionLabel, { marginTop: 20 }]}>Quick Links</Text>
      <View style={styles.card}>
        {[
          { label: 'Analytics',  icon: '📈', path: '/analytics' },
          { label: 'Invoices',   icon: '🧾', path: '/invoices' },
          { label: 'Billing',    icon: '💳', path: '/billing' },
        ].map((item, i, arr) => (
          <React.Fragment key={item.path}>
            <TouchableOpacity style={styles.linkBtn} onPress={() => Linking.openURL(`${BASE_URL}${item.path}`)}>
              <Text style={styles.linkBtnIcon}>{item.icon}</Text>
              <Text style={styles.linkBtnText}>{item.label}</Text>
              <Text style={styles.chevron}>›</Text>
            </TouchableOpacity>
            {i < arr.length - 1 && <View style={styles.divider} />}
          </React.Fragment>
        ))}
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  root:         { flex: 1, backgroundColor: COLORS.bg },
  body:         { padding: 20, paddingBottom: 40 },
  center:       { flex: 1, justifyContent: 'center', alignItems: 'center' },
  sectionLabel: { fontSize: 11, fontWeight: '700', color: COLORS.muted, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 10 },
  statsRow:     { flexDirection: 'row', gap: 10 },
  statCard:     { flex: 1, backgroundColor: '#fff', borderRadius: 14, padding: 14, alignItems: 'center', borderWidth: 1, borderColor: COLORS.border, ...SHADOW_CARD },
  statIcon:     { fontSize: 22, marginBottom: 6 },
  statVal:      { fontSize: 18, fontWeight: '800', color: COLORS.text },
  statLbl:      { fontSize: 10, color: COLORS.muted, fontWeight: '600', textTransform: 'uppercase', marginTop: 2 },
  card:         { backgroundColor: '#fff', borderRadius: 14, borderWidth: 1, borderColor: COLORS.border, overflow: 'hidden', ...SHADOW_CARD },
  linkBtn:      { flexDirection: 'row', alignItems: 'center', padding: 16, gap: 12 },
  linkBtnIcon:  { fontSize: 20, width: 26, textAlign: 'center' },
  linkBtnText:  { flex: 1, fontSize: 15, fontWeight: '600', color: COLORS.text },
  chevron:      { fontSize: 20, color: COLORS.muted },
  divider:      { height: 1, backgroundColor: COLORS.border, marginHorizontal: 16 },
});
