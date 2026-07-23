import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ProtectedRoute } from "../routes/ProtectedRoute";
import { AppShell } from "./AppShell";
import { DashboardScreen } from "../screens/Dashboard";
import { EntitiesScreen } from "../screens/Entities";
import { MeetingsScreen } from "../screens/Meetings";
import { MeetingWorkspace } from "../screens/MeetingWorkspace";
import { DocumentsScreen } from "../screens/Documents";
import { DocumentReader } from "../screens/DocumentReader";
import { DirectorsScreen } from "../screens/Directors";
import { DirectorProfile } from "../screens/DirectorProfile";
import { RegistersScreen } from "../screens/Registers";
import { InterestsScreen } from "../screens/Interests";
import { InterestDetail } from "../screens/InterestDetail";
import { MinuteBookScreen } from "../screens/MinuteBook";
import { CommitteesScreen } from "../screens/Committees";
import { ComplianceScreen } from "../screens/Compliance";
import { DelegationMatrixScreen } from "../screens/DelegationMatrix";
import { GroupScreen } from "../screens/Group";
import { AnnouncementsScreen } from "../screens/Announcements";
import { SearchScreen } from "../screens/Search";
import { AccessScreen } from "../screens/Access";
import { MinutesEditor, MinutesList } from "../screens/Minutes";
import { ResolutionsScreen } from "../screens/Resolutions";
import { ActionsScreen } from "../screens/Actions";
import { NotificationsScreen } from "../screens/Notifications";
import { AuditScreen } from "../screens/Audit";
import { SettingsScreen } from "../screens/Settings";
import { Login } from "../screens/Login";
import { Mfa } from "../screens/Mfa";

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/mfa" element={<Mfa />} />
        <Route
          element={
            <ProtectedRoute>
              <AppShell />
            </ProtectedRoute>
          }
        >
          <Route path="/" element={<DashboardScreen />} />
          <Route path="group" element={<GroupScreen />} />
          <Route path="search" element={<SearchScreen />} />
          <Route path="entities" element={<EntitiesScreen />} />
          <Route path="meetings" element={<MeetingsScreen />} />
          <Route path="meetings/:id" element={<MeetingWorkspace />} />
          <Route path="documents" element={<DocumentsScreen />} />
          <Route path="documents/:id" element={<DocumentReader />} />
          <Route path="directors" element={<DirectorsScreen />} />
          <Route path="directors/:id" element={<DirectorProfile />} />
          <Route path="registers" element={<RegistersScreen />} />
          <Route path="interests" element={<InterestsScreen />} />
          <Route path="interests/:id" element={<InterestDetail />} />
          <Route path="access" element={<AccessScreen />} />
          <Route path="minutes" element={<MinutesList />} />
          <Route path="minute-book" element={<MinuteBookScreen />} />
          <Route path="committees" element={<CommitteesScreen />} />
          <Route path="compliance" element={<ComplianceScreen />} />
          <Route path="delegation" element={<DelegationMatrixScreen />} />
          <Route path="meetings/:id/minutes" element={<MinutesEditor />} />
          <Route path="resolutions" element={<ResolutionsScreen />} />
          <Route path="actions" element={<ActionsScreen />} />
          <Route path="notifications" element={<NotificationsScreen />} />
          <Route path="announcements" element={<AnnouncementsScreen />} />
          <Route path="audit" element={<AuditScreen />} />
          <Route path="settings" element={<SettingsScreen />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
