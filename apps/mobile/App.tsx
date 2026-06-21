import { StatusBar } from 'expo-status-bar';
import { SafeAreaView, StyleSheet, Text, View } from 'react-native';

export default function App() {
  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      <View style={styles.hero}>
        <Text style={styles.kicker}>SARATHI</Text>
        <Text style={styles.title}>Citizen services in one secure app.</Text>
        <Text style={styles.body}>
          Mobile entry point for document intake, tax guidance, application tracking,
          workflow updates, and official notifications.
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#07111f',
  },
  hero: {
    flex: 1,
    justifyContent: 'center',
    padding: 24,
  },
  kicker: {
    color: '#8bd3ff',
    fontSize: 14,
    letterSpacing: 2,
    textTransform: 'uppercase',
    marginBottom: 12,
  },
  title: {
    color: '#ffffff',
    fontSize: 40,
    fontWeight: '700',
    lineHeight: 48,
    marginBottom: 16,
  },
  body: {
    color: '#c8d5e8',
    fontSize: 18,
    lineHeight: 28,
    maxWidth: 560,
  },
});
