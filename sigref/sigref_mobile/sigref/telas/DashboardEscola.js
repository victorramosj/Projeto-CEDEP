import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
  RefreshControl,
  Image,
  TouchableOpacity // Importe TouchableOpacity
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { useRoute, useNavigation } from '@react-navigation/native';

const API_BASE_URL = 'http://10.0.2.2:8000';
const SCHOOL_DASHBOARD_CACHE_KEY = '@school_dashboard_cache_';

const SchoolDashboardScreen = () => {
  const route = useRoute();
  const navigation = useNavigation();
  const { escolaId, userData } = route.params;

  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);

  const loadDashboardFromCache = useCallback(async () => {
    try {
      const cachedData = await AsyncStorage.getItem(`${SCHOOL_DASHBOARD_CACHE_KEY}${escolaId}`);
      if (cachedData) {
        setDashboardData(JSON.parse(cachedData));
      }
    } catch (e) {
      console.error('Erro ao carregar cache:', e);
    }
  }, [escolaId]);

  const fetchDashboardData = useCallback(async () => {
    setRefreshing(true);
    try {
      const netInfoState = await NetInfo.fetch();
      setIsOffline(!netInfoState.isConnected);
      if (!netInfoState.isConnected) return;

      const token = userData?.token;
      if (!token) {
        navigation.replace('Login');
        return;
      }

      const url = `${API_BASE_URL}/monitoramento/api/escola-dashboard/${escolaId}/`;
      const response = await axios.get(url, {
        headers: { 'Authorization': `Token ${token}` }
      });

      setDashboardData(response.data);
      await AsyncStorage.setItem(`${SCHOOL_DASHBOARD_CACHE_KEY}${escolaId}`, JSON.stringify(response.data));
    } catch (error) {
      console.error('Erro ao buscar dados:', error);
      setIsOffline(true);
    } finally {
      setRefreshing(false);
    }
  }, [escolaId, userData, navigation]);

  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await loadDashboardFromCache();
      setLoading(false);
      fetchDashboardData();
    };
    initializeData();
  }, [loadDashboardFromCache, fetchDashboardData]);

  const onRefresh = useCallback(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  // --- Funções de navegação para os novos botões ---
  const handleRelatarProblema = () => {
    navigation.navigate('RelatarProblemaScreen', { escolaId: escolaId, userData: userData });
  };

  const handleRelatarLacuna = () => {
    navigation.navigate('RelatarLacunaScreen', { escolaId: escolaId, userData: userData });
  };
  // --- Fim das funções de navegação ---


  if (loading || !dashboardData) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>Carregando dados da escola...</Text>
      </View>
    );
  }

  const escola = dashboardData.escola;
  const lacunasStats = dashboardData.lacunas_stats;
  const problemasStats = dashboardData.problemas_stats;
  const avisos = dashboardData.avisos;

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.contentContainer}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>Modo offline - Dados podem estar desatualizados</Text>
        </View>
      )}

      {/* Informações da Escola */}
      <View style={styles.headerEscola}>
        <View style={styles.infoEscola}>
          <Text style={styles.escolaTitle}>{escola.nome} - {escola.inep}</Text>

          <View style={styles.infoEscolaDetalhes}>
            <Text style={styles.detailText}>📍 {escola.endereco || "Endereço não cadastrado"}</Text>
            <Text style={styles.detailText}>📞 {escola.telefone || "Telefone não cadastrado"}</Text>
            <Text style={styles.detailText}>✉️ Email: {escola.email_escola}</Text>
            <Text style={styles.detailText}>👤 Gestor: {escola.nome_gestor}</Text>
            <Text style={styles.detailText}>📞 Telefone Gestor: {escola.telefone_gestor || "Não cadastrado"}</Text>

          </View>
        </View>

        <View style={styles.imagemEscola}>
          {escola.foto_fachada_url ? (
            <Image source={{ uri: escola.foto_fachada_url }} style={styles.schoolMainImage} />
          ) : (
            <Image source={require('../assets/default-school.jpeg')} style={styles.schoolMainImage} />
          )}
        </View>
      </View>

      {/* Indicadores Principais */}
      <View style={styles.row}>
        <View style={styles.cardIndicador}>
          <Text style={styles.cardIndicadorText}>LACUNAS EXISTENTES</Text>
          <Text style={styles.cardIndicadorValue}>{lacunasStats.total}</Text>
        </View>

        <View style={styles.cardIndicador}>
          <Text style={styles.cardIndicadorText}>PROBLEMAS EXISTENTES</Text>
          <Text style={styles.cardIndicadorValue}>{problemasStats.total}</Text>
        </View>
      </View>

      {/* Nova Seção: Botões de Relatar */}
      <View style={styles.reportButtonsSection}>
        <TouchableOpacity
          style={[styles.reportButton, styles.reportProblemaButton]}
          onPress={handleRelatarProblema}
        >
          <Text style={styles.reportButtonText}>Relatar Problema</Text>
        </TouchableOpacity>

        <TouchableOpacity
          style={[styles.reportButton, styles.reportLacunaButton]}
          onPress={handleRelatarLacuna}
        >
          <Text style={styles.reportButtonText}>Relatar Lacuna</Text>
        </TouchableOpacity>
      </View>
      {/* Fim da Nova Seção */}

      {/* Avisos Importantes */}
      <View style={styles.avisosImportantes}>
        <Text style={styles.avisosTitle}>AVISOS IMPORTANTES</Text>

        {avisos && avisos.length > 0 ? (
          avisos.slice(0, 3).map(aviso => (
            <View key={aviso.id} style={styles.avisoItem}>
              <Text style={styles.avisoTitulo}>{aviso.titulo}</Text>
              <Text style={styles.avisoMensagem}>{aviso.mensagem}</Text>
              <Text style={styles.avisoData}>
                {new Date(aviso.data_criacao).toLocaleDateString('pt-BR')}
              </Text>
            </View>
          ))
        ) : (
          <Text style={styles.noAvisosText}>Nenhum aviso no momento</Text>
        )}
      </View>

      {/* Estatísticas de Problemas */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ESTATÍSTICAS DE PROBLEMAS</Text>
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{problemasStats.resolvidos}</Text>
            <Text style={styles.statLabel}>Resolvidos</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{problemasStats.pendentes}</Text>
            <Text style={styles.statLabel}>Pendentes</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{problemasStats.em_andamento}</Text>
            <Text style={styles.statLabel}>Em Andamento</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{problemasStats.este_mes}</Text>
            <Text style={styles.statLabel}>Este Mês</Text>
          </View>
        </View>
      </View>

      {/* Estatísticas de Lacunas */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>ESTATÍSTICAS DE LACUNAS</Text>
        <View style={styles.statsContainer}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{lacunasStats.resolvidas}</Text>
            <Text style={styles.statLabel}>Resolvidas</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{lacunasStats.pendentes}</Text>
            <Text style={styles.statLabel}>Pendentes</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{lacunasStats.em_andamento}</Text>
            <Text style={styles.statLabel}>Em Andamento</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{lacunasStats.este_mes}</Text>
            <Text style={styles.statLabel}>Este Mês</Text>
          </View>
        </View>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  contentContainer: {
    padding: 16,
    paddingBottom: 30,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#333',
  },
  offlineBanner: {
    backgroundColor: '#ffcc00',
    padding: 10,
    borderRadius: 8,
    marginBottom: 16,
    alignItems: 'center',
  },
  offlineText: {
    color: '#333',
    fontWeight: 'bold',
  },
  headerEscola: {
    backgroundColor: '#fff',
    borderRadius: 12,
    marginBottom: 24,
    elevation: 3,
    overflow: 'hidden',
  },
  infoEscola: {
    padding: 20,
  },
  escolaTitle: {
    color: '#26326D',
    fontSize: 22,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  infoEscolaDetalhes: {
    marginBottom: 16,
  },
  detailText: {
    fontSize: 15,
    color: '#546E7A',
    marginBottom: 8,
  },
  imagemEscola: {
    width: '100%',
    height: 200,
  },
  schoolMainImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 24,
  },
  cardIndicador: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    width: '48%',
    elevation: 2,
    alignItems: 'center',
  },
  cardIndicadorText: {
    color: '#546E7A',
    fontWeight: '500',
    fontSize: 14,
    marginBottom: 8,
    textAlign: 'center',
  },
  cardIndicadorValue: {
    fontSize: 36,
    fontWeight: '700',
    color: '#26326D',
  },
  avisosImportantes: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
    elevation: 2,
  },
  avisosTitle: {
    color: '#E53935',
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 16,
  },
  avisoItem: {
    marginBottom: 16,
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  avisoTitulo: {
    fontWeight: 'bold',
    fontSize: 16,
    marginBottom: 8,
    color: '#263238',
  },
  avisoMensagem: {
    color: '#546E7A',
    fontSize: 14,
    marginBottom: 8,
  },
  avisoData: {
    fontSize: 12,
    color: '#90A4AE',
    textAlign: 'right',
  },
  noAvisosText: {
    color: '#90A4AE',
    textAlign: 'center',
    fontStyle: 'italic',
    paddingVertical: 16,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
    elevation: 2,
  },
  sectionTitle: {
    color: '#263238',
    fontWeight: 'bold',
    fontSize: 18,
    marginBottom: 16,
  },
  statsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
  },
  statItem: {
    width: '48%',
    backgroundColor: '#F5F7FA',
    borderRadius: 8,
    padding: 16,
    marginBottom: 16,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    color: '#26326D',
    marginBottom: 8,
  },
  statLabel: {
    fontSize: 14,
    color: '#546E7A',
    textAlign: 'center',
  },
  // --- Novos estilos para os botões de relatar ---
  reportButtonsSection: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 24,
    gap: 15, // Espaçamento entre os botões
  },
  reportButton: {
    flex: 1, // Faz com que os botões ocupem o espaço disponível igualmente
    paddingVertical: 15,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 3,
  },
  reportProblemaButton: {
    backgroundColor: '#FF6F00', // Um laranja vibrante para problemas
  },
  reportLacunaButton: {
    backgroundColor: '#00B0FF', // Um azul claro para lacunas
  },
  reportButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  // --- Fim dos novos estilos ---
});

export default SchoolDashboardScreen;