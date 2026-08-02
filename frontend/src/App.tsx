import { Routes, Route } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import HomePage from "./pages/Homepage";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";


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

            </Route>

        </Routes>

    );
}
export default App;