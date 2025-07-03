import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { StyleSheet, Text, View } from 'react-native'; // Importações adicionadas
import LoginScreen from './telas/LoginScreen.js';

const Stack = createStackNavigator();

const HomeScreen = ({ route }) => {
  const { userData } = route.params;
  
  return (
    <View style={styles.container}>
      <Text style={styles.welcome}>Bem-vindo, {userData.fullName}!</Text>
      <Text>Tipo de usuário: {userData.userTypeDisplay} ({userData.userType})</Text>
      <Text>Nível de acesso: {userData.accessLevel}</Text>
      {userData.email && <Text>Email: {userData.email}</Text>}
      {userData.celular && <Text>Celular: {userData.celular}</Text>}

      {userData.setor && (
        <View style={styles.infoSection}>
          <Text style={styles.sectionTitle}>Informações do Setor:</Text>
          <Text>Setor: {userData.setor.nome}</Text>
          <Text>Hierarquia: {userData.setor.hierarquia_completa}</Text>
        </View>
      )}

      {userData.escolas && userData.escolas.length > 0 && (
        <View style={styles.infoSection}>
          <Text style={styles.sectionTitle}>Escolas Associadas:</Text>
          {userData.escolas.map((escola, index) => (
            <Text key={escola.id}>- {escola.nome} (INEP: {escola.inep})</Text>
          ))}
        </View>
      )}

      {/* Exemplo de renderização condicional por tipo de usuário */}
      {userData.userType === 'ESCOLA' && (
        <Text style={styles.alertText}>Você tem acesso como usuário de Escola.</Text>
      )}
      {userData.userType === 'ADMIN' && (
        <Text style={styles.alertText}>Você tem acesso como Administrador.</Text>
      )}

    </View>
  );
};

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Login">
        <Stack.Screen 
          name="Login" 
          component={LoginScreen} 
          options={{ headerShown: false }} 
        />
        <Stack.Screen 
          name="Home" 
          component={HomeScreen} 
          options={{ title: 'Dashboard' }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20
  },
  welcome: {
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15
  },
  infoSection: {
    marginTop: 20,
    padding: 10,
    backgroundColor: '#e0e0e0',
    borderRadius: 8,
    width: '100%',
    alignItems: 'center'
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 5
  },
  alertText: {
    marginTop: 20,
    color: 'blue',
    fontStyle: 'italic'
  }
});
