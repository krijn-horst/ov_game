import {
    createContext,
    useContext,
    useState
} from "react";

import type { ReactNode } from "react";

interface User {
    username: string;
    email: string;
    password: string;
}

interface AuthContextType {

    user: User | null;
    isGuest: boolean;

    login: (
        username: string,
        password: string
    ) => boolean;

    register: (
        username: string,
        email: string,
        password: string
    ) => string | null;

    continueAsGuest: () => void;
    logout: () => void;
}

const AuthContext = createContext<
    AuthContextType | undefined
>(undefined);

export const AuthProvider = ({
    children
}: {
    children: ReactNode
}) => {

    const storedUser =
        sessionStorage.getItem("currentUser");

    const [user, setUser] =
        useState<User | null>(
            storedUser
            ? JSON.parse(storedUser)
            : null
        );

    const storedGuest =
        sessionStorage.getItem("guest");


    const [isGuest, setIsGuest] =
        useState(storedGuest === "true");

    const login = (
        username: string,
        password: string
    ) => {

        const users = JSON.parse(
            sessionStorage.getItem("users") || "[]"
        );

        const foundUser = users.find(
            (u: User) =>
                u.username === username &&
                u.password === password
        );

        if (!foundUser) {
            return false;
        }

        sessionStorage.setItem(
            "currentUser",
            JSON.stringify(foundUser)
        );

        sessionStorage.removeItem(
            "guest"
        );
        setIsGuest(false);

        setUser(foundUser);

        return true;
    };

    const register = (
        username: string,
        email: string,
        password: string
    ) => {

        const users = JSON.parse(
            sessionStorage.getItem("users") || "[]"
        );

        if (
            users.some(
                (u: User) =>
                    u.username === username
            )
        ) {
            return "Username already exists";
        }

        if (
            users.some(
                (u: User) =>
                    u.email === email
            )
        ) {
            return "Email already exists";
        }

        const newUser = {
            username,
            email,
            password
        };

        users.push(newUser);

        sessionStorage.setItem(
            "users",
            JSON.stringify(users)
        );

        return null;
    };

    const continueAsGuest = () => {
            sessionStorage.setItem(
                "guest",
                "true"
            );
            setIsGuest(true);
        };

        const logout = () => {

        sessionStorage.removeItem(
            "currentUser"
        );

        sessionStorage.removeItem(
            "guest"
        );

        setUser(null);
        setIsGuest(false);
    };

    return (

        <AuthContext.Provider
            value={{
                user,
                isGuest,
                login,
                register,
                continueAsGuest,
                logout
            }}
        >
            {children}
        </AuthContext.Provider>

    );

};


export const useAuth = () => {
    const context = useContext(
        AuthContext
    );

    if (!context) {
        throw new Error(
            "useAuth must be used inside AuthProvider"
        );
    }

    return context;
};