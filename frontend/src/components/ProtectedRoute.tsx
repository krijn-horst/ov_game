import { Navigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

interface ProtectedRouteProps {
    children: React.ReactNode;
}

const ProtectedRoute = ({
    children
}: ProtectedRouteProps) => {

    const {
        user,
        isGuest
    } = useAuth();

    if (!user && !isGuest) {
        return (
            <Navigate
                to="/login"
                replace
            />
        );
    }

    return children;
};
export default ProtectedRoute;