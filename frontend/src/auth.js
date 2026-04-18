// Gerenciamento de token JWT no localStorage.
const KEY = "cubo_captura_token";
const USER_KEY = "cubo_captura_user";

export const auth = {
  getToken: () => localStorage.getItem(KEY),
  setToken: (t) => localStorage.setItem(KEY, t),
  clear: () => {
    localStorage.removeItem(KEY);
    localStorage.removeItem(USER_KEY);
  },

  getUser: () => {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  setUser: (u) => localStorage.setItem(USER_KEY, JSON.stringify(u)),

  isLogged: () => Boolean(localStorage.getItem(KEY)),
};
