import React from 'react';
import { StyleSheet, Text, View, TouchableOpacity, ScrollView } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Ionicons } from '@expo/vector-icons';

const HomeScreen = ({ route, navigation }) => {
  const { userData } = route.params;

  const handleLogout = async () => {
    try {
      await AsyncStorage.removeItem('userData');
      navigation.replace('Login');
    } catch (e) {
      console.error('Erro ao fazer logout:', e);
      alert('Ocorreu um erro ao tentar sair. Tente novamente.');
    }
  };

  // Função para determinar a cor do badge por tipo de usuário
  const getUserTypeColor = () => {
    switch(userData.userType) {
      case 'ADMIN': return '#dc3545';
      case 'ESCOLA': return '#1a73e8';
      case 'MONITOR': return '#0d6efd';
      default: return '#6c757d';
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Ionicons name="person" size={32} color="#fff" />
        </View>
        <Text style={styles.welcome}>Bem-vindo, {userData.fullName}!</Text>
      </View>

      {/* User Info Card */}
      <View style={styles.card}>
        <View style={styles.cardHeader}>
          <Text style={styles.cardTitle}>Informações do Usuário</Text>
          <View style={[styles.userTypeBadge, { backgroundColor: getUserTypeColor() }]}>
            <Text style={styles.badgeText}>{userData.userTypeDisplay}</Text>
          </View>
        </View>

        <View style={styles.infoRow}>
          <Ionicons name="key" size={16} color="#6c757d" />
          <Text style={styles.infoText}>Nível de acesso: {userData.accessLevel}</Text>
        </View>
        
        {userData.email && (
          <View style={styles.infoRow}>
            <Ionicons name="mail" size={16} color="#6c757d" />
            <Text style={styles.infoText}>{userData.email}</Text>
          </View>
        )}
        
        {userData.celular && (
          <View style={styles.infoRow}>
            <Ionicons name="call" size={16} color="#6c757d" />
            <Text style={styles.infoText}>{userData.celular}</Text>
          </View>
        )}
      </View>

      {/* Setor Section */}
      {userData.setor && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Setor</Text>
          <View style={styles.divider} />
          
          <View style={styles.infoRow}>
            <Ionicons name="business" size={16} color="#6c757d" />
            <Text style={styles.infoText}>{userData.setor.nome}</Text>
          </View>
          
          <View style={styles.infoRow}>
            <Ionicons name="git-network" size={16} color="#6c757d" />
            <Text style={styles.infoText}>{userData.setor.hierarquia_completa}</Text>
          </View>
        </View>
      )}

      {/* Escolas Section */}
      {userData.escolas && userData.escolas.length > 0 && (
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Escolas Associadas</Text>
          <View style={styles.divider} />
          
          {userData.escolas.map((escola, index) => (
            <View key={escola.id} style={styles.schoolItem}>
              <Ionicons name="school" size={16} color="#4e73df" />
              <View style={styles.schoolInfo}>
                <Text style={styles.schoolName}>{escola.nome}</Text>
                <Text style={styles.schoolDetail}>INEP: {escola.inep}</Text>
              </View>
            </View>
          ))}
        </View>
      )}

      {/* Actions */}
      <TouchableOpacity 
        style={styles.primaryButton}
        onPress={() => navigation.navigate('Calendar')}
      >
        <Ionicons name="calendar" size={20} color="#fff" />
        <Text style={styles.buttonText}>Ver Calendário de Eventos</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={styles.primaryButton}
        onPress={() => navigation.navigate('SelecaoEscolas')}
      >
        <Ionicons name="school" size={20} color="#fff" />
        <Text style={styles.buttonText}>Selecionar Escolas</Text>
      </TouchableOpacity>
      

      <TouchableOpacity
        style={styles.primaryButton}
        onPress={() => navigation.navigate('RelatarProblemas')}
      >
        <Ionicons name="alert-circle" size={20} color="#fff" />
        <Text style={styles.buttonText}>Relatar Problemas</Text>
      </TouchableOpacity>

      {/* Adicione mais botões conforme necessário, por exemplo: */}
      <TouchableOpacity style={styles.primaryButton} onPress={() => navigation.navigate('VisualizarQuestionario')}>
        <Ionicons name="eye" size={20} color="#fff" />
        <Text style={styles.buttonText}>Relatórios</Text>
      </TouchableOpacity> 
      <TouchableOpacity 
        style={styles.logoutButton} 
        onPress={handleLogout}
      >
        <Ionicons name="log-out" size={20} color="#dc3545" />
        <Text style={styles.logoutText}>Sair da Conta</Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#f8f9fc',
    padding: 20,
    paddingTop: 40,
  },
  header: {
    alignItems: 'center',
    marginBottom: 30,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#4e73df',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
  },
  welcome: {
    fontSize: 24,
    fontWeight: '700',
    color: '#2d3748',
    textAlign: 'center',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 6,
    elevation: 3,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 15,
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2d3748',
  },
  userTypeBadge: {
    paddingVertical: 4,
    paddingHorizontal: 12,
    borderRadius: 50,
  },
  badgeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  infoText: {
    marginLeft: 10,
    fontSize: 16,
    color: '#4a5568',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#2d3748',
    marginBottom: 5,
  },
  divider: {
    height: 1,
    backgroundColor: '#e2e8f0',
    marginVertical: 15,
  },
  schoolItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 15,
  },
  schoolInfo: {
    marginLeft: 10,
    flex: 1,
  },
  schoolName: {
    fontSize: 16,
    fontWeight: '500',
    color: '#2d3748',
  },
  schoolDetail: {
    fontSize: 14,
    color: '#718096',
  },
  primaryButton: {
    flexDirection: 'row',
    backgroundColor: '#4e73df',
    borderRadius: 10,
    padding: 16,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 15,
    shadowColor: '#4e73df',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 4,
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600',
    marginLeft: 10,
  },
  logoutButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 16,
    marginTop: 10,
  },
  logoutText: {
    color: '#dc3545',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 10,
  },
});

export default HomeScreen;