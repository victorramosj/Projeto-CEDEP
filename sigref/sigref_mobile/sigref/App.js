//expo start
import React, { useState, useEffect } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { ActivityIndicator, View, StyleSheet, Text } from 'react-native'; // Importe ActivityIndicator, View, Text
import AsyncStorage from '@react-native-async-storage/async-storage'; // Importe AsyncStorage
import NetInfo from '@react-native-community/netinfo'; // Importe NetInfo

import LoginScreen from './telas/LoginScreen.js';
import HomeScreen from './telas/HomeScreen.js'; 
import CalendarScreen from './telas/CalendarScreen.js';
import SelecaoEscolaScreen from './telas/SelecaoEscola.js';
import ResponderQuestionarioScreen from './telas/ResponderQuestionario.js';
import RelatarProblemaScreen from './telas/RelatarProblemaScreen.js';
import VisualizarQuestionarioScreen from './telas/VisualizarQuestionarios.js';
import DashboardEscolaScreen from './telas/DashboardEscola.js';
import GerarRelatorioPdfScreen from './telas/GerarRelatorioPdfScreen.js';
import RelatarLacunaScreen from './telas/RelatarLacunaScreen.js';

const Stack = createStackNavigator();

export default function App() {
  const [loading, setLoading] = useState(true);
  const [userData, setUserData] = useState(null);
  const [isConnected, setIsConnected] = useState(true); // Estado para a conexão de internet

  useEffect(() => {
    // Listener para o status da conexão de internet
    const unsubscribeNetInfo = NetInfo.addEventListener(state => {
      setIsConnected(state.isConnected);
      console.log("Status da conexão:", state.isConnected ? "Online" : "Offline");
    });

    const checkLoginStatus = async () => {
      try {
        const cachedUserData = await AsyncStorage.getItem('userData');
        if (cachedUserData) {
          setUserData(JSON.parse(cachedUserData));
        }
      } catch (e) {
        console.error('Erro ao carregar dados do usuário do cache:', e);
      } finally {
        setLoading(false);
      }
    };

    checkLoginStatus();

    // Limpa o listener ao desmontar o componente
    return () => unsubscribeNetInfo();
  }, []);

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#0000ff" />
        <Text style={styles.loadingText}>Verificando login...</Text>
      </View>
    );
  }

  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName={userData ? "Home" : "Login"}>
        <Stack.Screen 
          name="Login" 
          component={LoginScreen} 
          options={{ headerShown: false }} 
          initialParams={{ setIsConnected }} // Passa o estado da conexão para a tela de login
        />
        <Stack.Screen 
          name="Home" 
          component={HomeScreen} 
          options={{ headerShown: false }}
          initialParams={{ userData }} // Passa os dados do usuário para a HomeScreen
        />
        <Stack.Screen
          name="Calendar"
          component={CalendarScreen}
          options={{ title: 'Calendário de Eventos' }}
        />
        <Stack.Screen
          name="SelecaoEscolas"
          component={SelecaoEscolaScreen}
          options={{ title: 'Seleção de Escolas' }}
        />
        <Stack.Screen
          name="ResponderQuestionario"
          component={ResponderQuestionarioScreen}
          options={{ title: 'Responder Questionário' }}
        />        
        <Stack.Screen
          name="VisualizarQuestionario"
          component={VisualizarQuestionarioScreen}
          options={{ title: 'Visualizar Questionário' }}
        />
        <Stack.Screen
          name="DashboardEscola"
          component={DashboardEscolaScreen}
          options={{ title: 'Dashboard da Escola' }}
        />         
        <Stack.Screen
          name="RelatarProblemaScreen"
          component={RelatarProblemaScreen }
          options={{ title: 'Relatar Problema' }} /
          >
        <Stack.Screen name="RelatarLacunaScreen"
          component={RelatarLacunaScreen}
          options={{ title: 'Relatar Lacuna' }} 
          />
          <Stack.Screen name="GerarRelatorioPdfScreen"
          component={GerarRelatorioPdfScreen}
          options={{ title: 'GerarRelatorioPdfScreen' }} 
          />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
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
});
