import React, { useEffect, useState, useCallback } from "react";
import {
  SafeAreaView,
  ScrollView,
  View,
  Text,
  TextInput,
  TouchableOpacity,
  FlatList,
  StyleSheet,
  Alert,
  Platform,
  Linking,
} from "react-native";
import * as Device from "expo-device";
import Constants from "expo-constants";

const API_URL = "http://51.255.46.216:5000";

const NOTIFICATIONS_INDISPONIBLES =
  Constants.executionEnvironment === "storeClient" && Platform.OS === "android";

const Notifications = NOTIFICATIONS_INDISPONIBLES ? null : require("expo-notifications");

if (Notifications) {
  Notifications.setNotificationHandler({
    handleNotification: async () => ({
      shouldShowAlert: true,
      shouldPlaySound: true,
      shouldSetBadge: false,
    }),
  });
}

export default function App() {
  const [pushToken, setPushToken] = useState(null);
  const [recherches, setRecherches] = useState([]);
  const [motsCles, setMotsCles] = useState("");
  const [nom, setNom] = useState("");
  const [prixMax, setPrixMax] = useState("");
  const [marque, setMarque] = useState("");
  const [taille, setTaille] = useState("");
  const [chargement, setChargement] = useState(false);

  useEffect(() => {
    enregistrerPourNotifications().then(setPushToken);
    if (NOTIFICATIONS_INDISPONIBLES) return;
    const abonnement = Notifications.addNotificationResponseReceivedListener((reponse) => {
      const url = reponse.notification.request.content.data?.url;
      if (url) Linking.openURL(url);
    });
    return () => abonnement.remove();
  }, []);

  useEffect(() => {
    if (pushToken) chargerRecherches(pushToken);
  }, [pushToken]);

  async function enregistrerPourNotifications() {
    if (!Device.isDevice) return null;
    if (NOTIFICATIONS_INDISPONIBLES) {
      console.warn("Notifications indisponibles dans Expo Go sur Android (SDK 53+).");
      return null;
    }
    const { status: existant } = await Notifications.getPermissionsAsync();
    let statutFinal = existant;
    if (existant !== "granted") {
      const { status } = await Notifications.requestPermissionsAsync();
      statutFinal = status;
    }
    if (statutFinal !== "granted") return null;
    if (Platform.OS === "android") {
      await Notifications.setNotificationChannelAsync("default", {
        name: "default",
        importance: Notifications.AndroidImportance.HIGH,
      });
    }
    try {
      const projectId = Constants.expoConfig?.extra?.eas?.projectId;
      const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
      return token;
    } catch (e) {
      console.warn("Impossible d'obtenir le push token", e);
      return null;
    }
  }

  async function chargerRecherches(token) {
    try {
      const resp = await fetch(`${API_URL}/api/searches?push_token=${encodeURIComponent(token)}`);
      const data = await resp.json();
      setRecherches(Array.isArray(data) ? data : []);
    } catch (e) {
      console.warn("Impossible de charger les recherches", e);
    }
  }

  const ajouterRecherche = useCallback(async () => {
    if (!motsCles.trim()) {
      Alert.alert("Mots-clés manquants", "Indique au moins un mot-clé à rechercher.");
      return;
    }
    const identifiant = pushToken || `anonyme-${Device.osInternalBuildId || Date.now()}`;
    setChargement(true);
    try {
      await fetch(`${API_URL}/api/searches`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          push_token: identifiant,
          nom: nom || motsCles,
          mots_cles: motsCles,
          prix_max: prixMax ? parseFloat(prixMax) : null,
          marque: marque || null,
          taille: taille || null,
        }),
      });
      setMotsCles(""); setNom(""); setPrixMax(""); setMarque(""); setTaille("");
      chargerRecherches(identifiant);
    } catch (e) {
      Alert.alert("Erreur", "Impossible d'ajouter la recherche.");
    } finally {
      setChargement(false);
    }
  }, [pushToken, motsCles, nom, prixMax, marque, taille]);

  const supprimerRecherche = useCallback(async (id) => {
    const identifiant = pushToken || `anonyme-${Device.osInternalBuildId || Date.now()}`;
    try {
      await fetch(`${API_URL}/api/searches/${id}?push_token=${encodeURIComponent(identifiant)}`, { method: "DELETE" });
      chargerRecherches(identifiant);
    } catch (e) {
      Alert.alert("Erreur", "Impossible de supprimer la recherche.");
    }
  }, [pushToken]);

  return (
    <SafeAreaView style={styles.conteneur}>
      <ScrollView contentContainerStyle={styles.scroll}>
        <Text style={styles.titre}>🔎 Alertes Vinted</Text>
        <View style={styles.formulaire}>
          <TextInput style={styles.champ} placeholder="Mots-clés (ex: nike air max)" placeholderTextColor="#64748b" value={motsCles} onChangeText={setMotsCles} />
          <TextInput style={styles.champ} placeholder="Nom de la recherche (optionnel)" placeholderTextColor="#64748b" value={nom} onChangeText={setNom} />
          <TextInput style={styles.champ} placeholder="Prix max en € (optionnel)" placeholderTextColor="#64748b" value={prixMax} onChangeText={setPrixMax} keyboardType="numeric" />
          <TextInput style={styles.champ} placeholder="Marque (optionnel)" placeholderTextColor="#64748b" value={marque} onChangeText={setMarque} />
          <TextInput style={styles.champ} placeholder="Taille (optionnel)" placeholderTextColor="#64748b" value={taille} onChangeText={setTaille} />
          <TouchableOpacity style={styles.bouton} onPress={ajouterRecherche} disabled={chargement}>
            <Text style={styles.boutonTexte}>{chargement ? "Ajout..." : "➕ Ajouter la recherche"}</Text>
          </TouchableOpacity>
        </View>
        <Text style={styles.sousTitre}>Mes recherches actives</Text>
        <FlatList
          data={recherches}
          keyExtractor={(item) => String(item.id)}
          scrollEnabled={false}
          renderItem={({ item }) => (
            <View style={styles.carte}>
              <View style={{ flex: 1 }}>
                <Text style={styles.carteTitre}>{item.nom}</Text>
                <Text style={styles.carteDetail}>
                  {item.mots_cles}{item.prix_max ? ` · max ${item.prix_max}€` : ""}{item.marque ? ` · ${item.marque}` : ""}{item.taille ? ` · taille ${item.taille}` : ""}
                </Text>
              </View>
              <TouchableOpacity onPress={() => supprimerRecherche(item.id)}>
                <Text style={styles.supprimer}>🗑️</Text>
              </TouchableOpacity>
            </View>
          )}
          ListEmptyComponent={<Text style={styles.vide}>Aucune recherche pour l'instant.</Text>}
        />
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  conteneur: { flex: 1, backgroundColor: "#0f172a" },
  scroll: { padding: 20, paddingTop: 60, paddingBottom: 60 },
  titre: { fontSize: 26, fontWeight: "700", color: "#fff", marginBottom: 20 },
  formulaire: { backgroundColor: "#1e293b", borderRadius: 14, padding: 16, marginBottom: 24 },
  champ: { backgroundColor: "#0f172a", color: "#fff", borderRadius: 8, paddingHorizontal: 12, paddingVertical: 10, marginBottom: 10, borderWidth: 1, borderColor: "#334155" },
  bouton: { backgroundColor: "#22c55e", borderRadius: 8, paddingVertical: 12, alignItems: "center", marginTop: 4 },
  boutonTexte: { color: "#04240f", fontWeight: "700" },
  sousTitre: { fontSize: 18, fontWeight: "600", color: "#fff", marginBottom: 10 },
  carte: { flexDirection: "row", alignItems: "center", backgroundColor: "#1e293b", borderRadius: 12, padding: 14, marginBottom: 10 },
  carteTitre: { color: "#fff", fontWeight: "600", fontSize: 15 },
  carteDetail: { color: "#94a3b8", marginTop: 4, fontSize: 13 },
  supprimer: { fontSize: 18, marginLeft: 10 },
  vide: { color: "#64748b", fontStyle: "italic" },
});
