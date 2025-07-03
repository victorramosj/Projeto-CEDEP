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
  Image, // Para exibir a foto da fachada
  Alert // Para mensagens de erro
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import NetInfo from '@react-native-community/netinfo';
import axios from 'axios';
import { useNavigation } from '@react-navigation/native'; // Para navegação

// URL base da sua API Django
// const API_BASE_URL = 'http://127.0.0.1:8000'; //para pc
const API_BASE_URL = 'http://10.0.2.2:8000'; //para emulador android
//const API_BASE_URL = 'https://grefloresta.com.br'; //URL do servidor remoto

// Chave para o cache do AsyncStorage
const SCHOOLS_CACHE_KEY = '@schools_cache';

const SchoolSelectionScreen = () => {
  const navigation = useNavigation();
  const [schools, setSchools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isOffline, setIsOffline] = useState(false);
  const [searchQuery, setSearchQuery] = useState(''); // Estado para o termo de busca

  // Função para carregar escolas do cache
  const loadSchoolsFromCache = useCallback(async () => {
    try {
      const cachedSchools = await AsyncStorage.getItem(SCHOOLS_CACHE_KEY);
      if (cachedSchools) {
        setSchools(JSON.parse(cachedSchools));
        console.log('Escolas carregadas do cache.');
      } else {
        console.log('Nenhuma escola encontrada no cache.');
      }
    } catch (e) {
      console.error('Erro ao carregar escolas do cache:', e);
    }
  }, []);

  // Função para buscar escolas da API
  const fetchSchools = useCallback(async (query = '', showAlert = true) => {
    setRefreshing(true);
    try {
      const netInfoState = await NetInfo.fetch();
      setIsOffline(!netInfoState.isConnected);

      if (!netInfoState.isConnected) {
        if (showAlert) {
          Alert.alert('Modo Offline', 'Você está offline. Exibindo dados em cache. Conecte-se à internet para atualizar.');
        }
        return;
      }

      // --- INÍCIO DA ADIÇÃO PARA AUTENTICAÇÃO ---
      // 1. Recupera o token do AsyncStorage
      const userDataString = await AsyncStorage.getItem('userData');
      const userData = userDataString ? JSON.parse(userDataString) : null;
      const token = userData ? userData.token : null;

      if (!token) {
        // Se não houver token, alerta o usuário e redireciona para o login
        Alert.alert('Erro de Autenticação', 'Token de autenticação não encontrado. Por favor, faça login novamente.');
        navigation.replace('Login'); 
        return; // Interrompe a execução
      }
      // --- FIM DA ADIÇÃO PARA AUTENTICAÇÃO ---

      const response = await axios.get(`${API_BASE_URL}/monitoramento/api/escolas-selection/`, {
        params: { q: query },
        headers: {
          'Authorization': `Token ${token}` // 2. Inclui o token no cabeçalho Authorization
        }
      });
      
      setSchools(response.data);
      await AsyncStorage.setItem(SCHOOLS_CACHE_KEY, JSON.stringify(response.data));
      console.log('Escolas atualizadas da API e salvas no cache.');

    } catch (error) {
      console.error('Erro ao buscar escolas da API:', error);
      if (error.response && error.response.status === 403) {
        // Se o servidor retornar 403 (Forbidden), pode ser token inválido ou sem permissão
        Alert.alert('Acesso Negado', 'Você não tem permissão para acessar esta funcionalidade. Por favor, faça login novamente.');
        navigation.replace('Login'); // Redireciona para login
      } else if (error.response && error.response.status === 401) {
        // Se o servidor retornar 401 (Unauthorized), pode ser token expirado ou inválido
        Alert.alert('Sessão Expirada', 'Sua sessão expirou. Por favor, faça login novamente.');
        navigation.replace('Login'); // Redireciona para login
      } else {
        Alert.alert('Erro', 'Não foi possível carregar as escolas. Verifique a conexão ou tente novamente.');
      }
      setIsOffline(true);
    } finally {
      setRefreshing(false);
    }
  }, [navigation]); // Adiciona navigation às dependências do useCallback

  useEffect(() => {
    const initializeData = async () => {
      setLoading(true);
      await loadSchoolsFromCache(); // Carrega do cache primeiro
      setLoading(false); // Desativa o loading para exibir o cache

      // Tenta buscar da rede em segundo plano (sem alerta inicial de offline)
      fetchSchools('', false); 
    };

    initializeData();
  }, [loadSchoolsFromCache, fetchSchools]);

  // Efeito para lidar com a busca
  useEffect(() => {
    const delayDebounceFn = setTimeout(() => {
      fetchSchools(searchQuery, false); // Busca com delay para evitar muitas requisições
    }, 500); // Delay de 500ms

    return () => clearTimeout(delayDebounceFn);
  }, [searchQuery, fetchSchools]); // Dispara a busca quando searchQuery muda

  const onRefresh = useCallback(() => {
    fetchSchools(searchQuery, true); // Puxar para atualizar sempre tenta buscar e alerta se offline
  }, [searchQuery, fetchSchools]);

  const renderSchoolItem = ({ item }) => (
    <TouchableOpacity 
      style={styles.schoolCard}
      // O onPress do card principal ainda pode ir para o Dashboard da Escola se desejar
      onPress={async () => {
        const userDataString = await AsyncStorage.getItem('userData');
        const userData = userDataString ? JSON.parse(userDataString) : null;
        if (userData) {
          navigation.navigate('DashboardEscola', { escolaId: item.id, userData: userData });
        } else {
          Alert.alert('Erro', 'Dados do usuário não encontrados. Por favor, faça login novamente.');
          navigation.replace('Login');
        }
      }}
    >
      {item.foto_fachada_url ? ( // Use foto_fachada_url
        <Image source={{ uri: item.foto_fachada_url }} style={styles.schoolImage} />
      ) : (
        <Image source={require('../assets/default-school.jpeg')} style={styles.schoolImage} />
      )}
      <View style={styles.cardBody}>
        <Text style={styles.schoolName}>{item.nome}</Text>
        <Text style={styles.schoolDetail}>INEP: {item.inep}</Text>
        <Text style={styles.schoolDetail}>Gestor: {item.nome_gestor}</Text>
        <View style={styles.buttonContainer}>
          {/* --- INÍCIO DA ALTERAÇÃO PARA NAVEGAR PARA QUESTIONÁRIOS --- */}
          <TouchableOpacity 
            style={styles.actionButtonPrimary}
            onPress={async () => { // Adicionado async aqui para await
              const userDataString = await AsyncStorage.getItem('userData');
              const userData = userDataString ? JSON.parse(userDataString) : null;
              if (userData) {
                // Redireciona para a tela de listagem de questionários da escola
                navigation.navigate('VisualizarQuestionario', { escolaId: item.id, userData: userData });
              } else {
                Alert.alert('Erro', 'Dados do usuário não encontrados. Por favor, faça login novamente.');
                navigation.replace('Login');
              }
            }}
          >
            <Text style={styles.buttonText}>Realizar Monitoramento</Text>
          </TouchableOpacity>
          {/* --- FIM DA ALTERAÇÃO PARA NAVEGAR PARA QUESTIONÁRIOS --- */}
          {/* Você pode adicionar o botão de relatório aqui, se o usuário não for monitor */}
          {/* <TouchableOpacity style={styles.actionButtonSecondary}>
            <Text style={styles.buttonText}>Relatório</Text>
          </TouchableOpacity> */}
        </View>
      </View>
    </TouchableOpacity>
  );

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>Carregando escolas...</Text>
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

      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="Buscar por nome, INEP ou gestor..."
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        <TouchableOpacity style={styles.searchButton}>
          <Text style={styles.searchButtonText}>Buscar</Text>
        </TouchableOpacity>
      </View>

      <FlatList
        data={schools}
        keyExtractor={(item) => item.id.toString()}
        renderItem={renderSchoolItem}
        contentContainerStyle={styles.flatListContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
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
  offlineBanner: {
    backgroundColor: '#ffcc00',
    padding: 10,
    borderRadius: 8,
    marginBottom: 10,
    alignItems: 'center',
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
    gap: 10,
  },
  actionButtonPrimary: {
    flex: 1,
    backgroundColor: '#007bff',
    paddingVertical: 8,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  actionButtonSecondary: {
    flex: 1,
    backgroundColor: '#6c757d',
    paddingVertical: 8,
    borderRadius: 5,
    alignItems: 'center',
    justifyContent: 'center',
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
