import { Route, Routes } from "react-router-dom";
import Navbar from "./components/Navbar";
import CreateTutorPage from "./pages/CreateTutorPage";
import EditTutorPage from "./pages/EditTutorPage";
import HomePage from "./pages/HomePage";
import NotFoundPage from "./pages/NotFoundPage";
import TutorDetailsPage from "./pages/TutorDetailsPage";
import TutorDirectoryPage from "./pages/TutorDirectoryPage";

function App() {
  return (
    <>
      <Navbar />

      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/tutors" element={<TutorDirectoryPage />} />
        <Route path="/tutors/new" element={<CreateTutorPage />} />
        <Route path="/tutors/:id" element={<TutorDetailsPage />} />
        <Route path="/tutors/:id/edit" element={<EditTutorPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Routes>
    </>
  );
}

export default App;