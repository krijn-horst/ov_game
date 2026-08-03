import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import HomePage from "./pages/Homepage";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import RoutePage from "./pages/RoutePage"

function App() {

    return (

        <Routes>

            <Route
                path="/login"
                element={<Login />}
            />

            <Route
                path="/register"
                element={<Register />}
            />

            <Route
                element={
                    <ProtectedRoute>
                        <Layout />
                    </ProtectedRoute>
                }
            >
                <Route
                    path="/home"
                    element={<HomePage />}
                />


            <Route
                path="/routes"
                element={<RoutePage />}
            />

            </Route>

        </Routes>

    );
}
export default App;