import React, { useEffect, useState, useCallback } from 'react';
import { View, Text, FlatList, StyleSheet, RefreshControl, ActivityIndicator, Alert } from 'react-native';
import Card from '../../components/Card';
import { parentGetNotes } from '../../services/api';
import { COLORS } from '../../theme';

function formatDate(str) {
  if (!str) return '';
  try { return new Date(str + 'T12:00:00').toLocaleDateString([], { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' }); } catch { return str; }
}

export default function ParentNotesScreen() {
  const [notes,      setNotes]      = useState([]);
  const [loading,    setLoading]    = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const res = await parentGetNotes();
      if (res.ok) setNotes(res.notes);
    } catch { Alert.alert('Error', 'Could not load notes.'); }
    finally { setLoading(false); setRefreshing(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={COLORS.primary} /></View>;

  return (
    <FlatList
      data={notes}
      keyExtractor={(_, i) => String(i)}
      style={styles.container}
      contentContainerStyle={{ padding: 16, paddingBottom: 48 }}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={COLORS.primary} />}
      ListEmptyComponent={<View style={styles.empty}><Text style={styles.emptyText}>No lesson notes yet.</Text></View>}
      renderItem={({ item }) => (
        <Card style={styles.noteCard}>
          <Text style={styles.noteDate}>{formatDate(item.date)}</Text>
          {!!item.notes && <Text style={styles.noteText}>{item.notes}</Text>}
          {!!item.assignment && (
            <View style={styles.assignmentBox}>
              <Text style={styles.assignmentLabel}>📌 Assignment</Text>
              <Text style={styles.assignmentText}>{item.assignment}</Text>
            </View>
          )}
        </Card>
      )}
    />
  );
}

const styles = StyleSheet.create({
  container:       { flex: 1, backgroundColor: COLORS.bg },
  center:          { flex: 1, justifyContent: 'center', alignItems: 'center' },
  noteCard:        { padding: 16, marginBottom: 10 },
  noteDate:        { fontSize: 12, fontWeight: '700', color: COLORS.primary, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.5 },
  noteText:        { fontSize: 15, color: COLORS.text, lineHeight: 22, marginBottom: 8 },
  assignmentBox:   { backgroundColor: COLORS.successBg, borderRadius: 10, padding: 12, marginTop: 4 },
  assignmentLabel: { fontSize: 12, fontWeight: '700', color: COLORS.success, marginBottom: 4 },
  assignmentText:  { fontSize: 14, color: COLORS.text, lineHeight: 20 },
  empty:           { alignItems: 'center', marginTop: 80 },
  emptyText:       { fontSize: 15, color: COLORS.muted },
});
