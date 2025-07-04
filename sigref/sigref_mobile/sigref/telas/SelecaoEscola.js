import React, { useState, useEffect, useCallback } from 'react';
import { 
  View, 
  Text, 
  StyleSheet, 
  ActivityIndicator, 
  FlatList, 
  RefreshControl,
  TextInput,
  TouchableOpacity,
  Image,
  Alert 
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { useNavigation } from '@react-navigation/native';
import useOfflineDataSync from './hooks/useOfflineDataSync'; // Importe o hook

// URL base da sua API Django
const API_BASE_URL = 'http://10.0.2.2:8000'; 

const SchoolSelectionScreen = () => {
  const navigation = useNavigation();
  const [schools, setSchools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Recupera userData do AsyncStorage para o hook
  const [storedUserData, setStoredUserData] = useState(null);
  useEffect(() => {
    const loadUserData = async () => {
      const dataString = await AsyncStorage.getItem('userData');
      setStoredUserData(dataString ? JSON.parse(dataString) : null);
    };
    loadUserData();
  }, []);

  // Usa o novo hook para gerenciar os dados offline
  const { offlineData, isSyncing, syncError, triggerMasterSync, isConnected: isGlobalConnected } = useOfflineDataSync(storedUserData);

  // A função fetchSchools agora usará os dados do hook (offlineData)
  const fetchSchools = useCallback(async (query = '') => {
    setRefreshing(true);
    setIsOffline(!isGlobalConnected);

    if (!isGlobalConnected) {
      Alert.alert('Modo Offline', 'Você está offline. Exibindo dados locais. Conecte-se à internet para buscar mais escolas.');
      const filteredOfflineSchools = offlineData.escolas.filter(school =>
        school.nome.toLowerCase().includes(query.toLowerCase()) ||
        school.inep.toLowerCase().includes(query.toLowerCase()) ||
        (school.nome_gestor && school.nome_gestor.toLowerCase().includes(query.toLowerCase())) // Adiciona verificação para nome_gestor
      );
      setSchools(filteredOfflineSchools);
      setLoading(false);
      setRefreshing(false);
      return;
    }

    console.log('Online: Buscando escolas filtradas da API...');
    try {
      const token = storedUserData?.token;
      if (!token) {
        Alert.alert('Erro de Autenticação', 'Token de autenticação não encontrado. Por favor, faça login novamente.');
        navigation.replace('Login'); 
        return;
      }

      const response = await axios.get(`${API_BASE_URL}/monitoramento/api/escolas-selection/`, {
        params: { q: query },
        headers: {
          'Authorization': `Token ${token}`
        }
      });
      
      setSchools(response.data);
      console.log('Escolas atualizadas da API.');

    } catch (error) {
      console.error('Erro ao buscar escolas da API:', error);
      if (error.response && (error.response.status === 403 || error.response.status === 401)) {
        Alert.alert('Acesso Negado', 'Você não tem permissão para acessar esta funcionalidade ou sua sessão expirou. Por favor, faça login novamente.');
        navigation.replace('Login');
      } else {
        Alert.alert('Erro', 'Não foi possível carregar as escolas. Verifique a conexão ou tente novamente.');
      }
      setIsOffline(true);
    } finally {
      setRefreshing(false);
      setLoading(false);
    }
  }, [searchQuery, isGlobalConnected, offlineData.escolas, storedUserData, navigation]);

  useEffect(() => {
    if (storedUserData) {
        setLoading(true);
        fetchSchools(searchQuery);
    }
  }, [storedUserData, fetchSchools]);

  const onRefresh = useCallback(() => {
    fetchSchools(searchQuery);
  }, [searchQuery, fetchSchools]);

  const renderSchoolItem = ({ item }) => (
    <TouchableOpacity 
      style={styles.schoolCard}
      onPress={async () => {
        const userDataString = await AsyncStorage.getItem('userData');
        const currentUserData = userDataString ? JSON.parse(userDataString) : null;
        if (currentUserData) {
          navigation.navigate('DashboardEscola', { escolaId: item.id, userData: currentUserData });
        } else {
          Alert.alert('Erro', 'Dados do usuário não encontrados. Por favor, faça login novamente.');
          navigation.replace('Login');
        }
      }}
    >
      {item.foto_fachada_url ? (
        <Image source={{ uri: item.foto_fachada_url }} style={styles.schoolImage} />
      ) : (
        <Image source={require('../assets/default-school.jpeg')} style={styles.schoolImage} />
      )}
      <View style={styles.cardBody}>
        <Text style={styles.schoolName}>{item.nome}</Text>
        <Text style={styles.schoolDetail}>INEP: {item.inep}</Text>
        <Text style={styles.schoolDetail}>Gestor: {item.nome_gestor}</Text>
        <View style={styles.buttonContainer}>
          <TouchableOpacity 
            style={styles.actionButtonPrimary}
            onPress={async () => {
              const userDataString = await AsyncStorage.getItem('userData');
              const currentUserData = userDataString ? JSON.parse(userDataString) : null;
              if (currentUserData) {
                navigation.navigate('VisualizarQuestionario', { escolaId: item.id, userData: currentUserData });
              } else {
                Alert.alert('Erro', 'Dados do usuário não encontrados. Por favor, faça login novamente.');
                navigation.replace('Login');
              }
            }}
          >
            <Text style={styles.buttonText}>Realizar Monitoramento</Text>
          </TouchableOpacity>

          {/* NOVO BOTÃO: Gerar Relatório PDF */}
          <TouchableOpacity 
            style={styles.actionButtonReport} // Novo estilo
            onPress={async () => {
              const userDataString = await AsyncStorage.getItem('userData');
              const currentUserData = userDataString ? JSON.parse(userDataString) : null;
              if (currentUserData) {
                navigation.navigate('GerarRelatorioPdfScreen', { escolaId: item.id, userData: currentUserData });
              } else {
                Alert.alert('Erro', 'Dados do usuário não encontrados. Por favor, faça login novamente.');
                navigation.replace('Login');
              }
            }}
          >
            <Text style={styles.buttonText}>Gerar Relatório PDF</Text>
          </TouchableOpacity>
          {/* FIM NOVO BOTÃO */}

        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading || isSyncing && !offlineData.escolas.length) { 
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>
          {isSyncing ? 'Sincronizando dados mestres...' : 'Carregando escolas...'}
        </Text>
        {syncError && <Text style={styles.errorText}>Erro de sincronização: {syncError}</Text>}
      </View>
    );
  }

  return (
    <View style={styles.container}>
      {isOffline && (
        <View style={styles.offlineBanner}>
          <Text style={styles.offlineText}>Você está offline. Dados podem estar desatualizados.</Text>
        </View>
      )}
      {syncError && !isOffline && (
        <View style={[styles.offlineBanner, styles.syncErrorBanner]}>
          <Text style={styles.offlineText}>Erro na sincronização: {syncError}</Text>
        </View>
      )}

      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar por nome, INEP ou gestor..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        <TouchableOpacity style={styles.searchButton} onPress={() => fetchSchools(searchQuery)}>
          <Text style={styles.searchButtonText}>Buscar</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={schools}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderSchoolItem}
        contentContainerStyle={styles.flatListContent}
        refreshControl={
          <RefreshControl refreshing={refreshing || isSyncing} onRefresh={onRefresh} />
        }
        ListEmptyComponent={() => (
          <Text style={styles.emptyListText}>Nenhuma escola encontrada.</Text>
        )}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    padding: 10,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#333',
  },
  errorText: {
    marginTop: 10,
    fontSize: 14,
    color: 'red',
    textAlign: 'center',
  },
  offlineBanner: {
    backgroundColor: '#ffcc00',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
  },
  syncErrorBanner: {
    backgroundColor: '#ffaaaa',
    borderColor: 'red',
    borderWidth: 1,
  },
  offlineText: {
    color: '#333',
    fontWeight: 'bold',
  },
  searchContainer: {
    flexDirection: 'row',
    marginBottom: 15,
  },
  searchInput: {
    flex: 1,
    height: 40,
    borderColor: '#ccc',
    borderWidth: 1,
    borderRadius: 8,
    paddingHorizontal: 10,
    marginRight: 10,
    backgroundColor: '#fff',
  },
  searchButton: {
    backgroundColor: '#007bff',
    paddingVertical: 10,
    paddingHorizontal: 15,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center',
  },
  searchButtonText: {
    color: '#fff',
    fontWeight: 'bold',
  },
  flatListContent: {
    paddingBottom: 20,
  },
  schoolCard: {
    backgroundColor: '#ffffff',
    borderRadius: 10,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    marginBottom: 15,
    overflow: 'hidden',
  },
  schoolImage: {
    width: '100%',
    height: 180,
    resizeMode: 'cover',
  },
  cardBody: {
    padding: 15,
  },
  schoolName: {
    fontSize: 18,
    fontWeight: 'bold',
    marginBottom: 5,
    color: '#333',
  },
  schoolDetail: {
    fontSize: 14,
    color: '#666',
    marginBottom: 3,
  },
  buttonContainer: {
    flexDirection: 'row',
    marginTop: 10,
    // gap: 10, // Removendo gap para usar marginHorizontal nos botões individuais para compatibilidade mais ampla
    justifyContent: 'space-between', // Para distribuir os botões
    flexWrap: 'wrap', // Permite quebrar linha se não houver espaço
  },
  actionButtonPrimary: {
    // flex: 1, // Removendo flex:1 para controlar melhor a largura se tiver muitos botões
    width: '48%', // Ajusta a largura para ter 2 por linha
    backgroundColor: '#007bff',
    paddingVertical: 8,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10, // Espaçamento entre as linhas de botões
  },
  actionButtonSecondary: {
    // flex: 1,
    width: '48%',
    backgroundColor: '#6c757d',
    paddingVertical: 8,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
  },
  // NOVO ESTILO para o botão de relatório
  actionButtonReport: {
    // flex: 1,
    width: '48%', // Ajusta a largura para ter 2 por linha
    backgroundColor: '#28a745', // Uma cor diferente, como verde para relatórios
    paddingVertical: 8,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10, // Espaçamento entre as linhas de botões
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 12,
    textAlign: 'center',
  },
  emptyListText: {
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
    color: '#888',
  },
});
export default SchoolSelectionScreen;