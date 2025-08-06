/**
 * Main Layout Component for Mass Tracking System
 * Provides navigation, header, and main content area
 */

import { useState } from 'react';
import { 
  Calendar, 
  BarChart3, 
  FileText, 
  Bell, 
  Settings, 
  LogOut, 
  Menu, 
  X,
  Home,
  Upload,
  Pause,
  Play,
  User
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuLabel, 
  DropdownMenuSeparator, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { useAuth, authUtils } from '@/lib/auth.jsx';
import '../App.css';

const Layout = ({ children, currentPage = 'dashboard' }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const userInfo = authUtils.formatUserInfo(user);

  const navigation = [
    { name: 'Dashboard', href: '#dashboard', icon: Home, id: 'dashboard' },
    { name: 'Mass Celebrations', href: '#celebrations', icon: Calendar, id: 'celebrations' },
    { name: 'Bulk Intentions', href: '#bulk-intentions', icon: Pause, id: 'bulk-intentions' },
    { name: 'Statistics', href: '#statistics', icon: BarChart3, id: 'statistics' },
    { name: 'Excel Import', href: '#import', icon: Upload, id: 'import' },
    { name: 'Notifications', href: '#notifications', icon: Bell, id: 'notifications' },
  ];

  const handleLogout = async () => {
    await logout();
    window.location.reload();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        >
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" />
        </div>
      )}

      {/* Sidebar */}
      <div className={`
        fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex items-center justify-between h-16 px-6 border-b border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <Calendar className="h-8 w-8 text-primary" />
            </div>
            <div className="ml-3">
              <h1 className="text-lg font-semibold text-gray-900">Mass Tracker</h1>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="lg:hidden"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        <nav className="mt-6 px-3">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = currentPage === item.id;
              return (
                <a
                  key={item.name}
                  href={item.href}
                  className={`
                    group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors
                    ${isActive 
                      ? 'bg-primary text-primary-foreground' 
                      : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900'
                    }
                  `}
                >
                  <item.icon className={`
                    mr-3 h-5 w-5 flex-shrink-0
                    ${isActive ? 'text-primary-foreground' : 'text-gray-400 group-hover:text-gray-500'}
                  `} />
                  {item.name}
                  {item.id === 'notifications' && (
                    <Badge variant="destructive" className="ml-auto">
                      3
                    </Badge>
                  )}
                </a>
              );
            })}
          </div>
        </nav>

        {/* User info in sidebar */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <div className="flex items-center">
            <Avatar className="h-8 w-8">
              <AvatarImage src={user?.profile_image_url} />
              <AvatarFallback>{userInfo.initials}</AvatarFallback>
            </Avatar>
            <div className="ml-3 flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {userInfo.name}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {userInfo.assignment || userInfo.email}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="flex items-center justify-between h-16 px-4 sm:px-6 lg:px-8">
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="sm"
                className="lg:hidden"
                onClick={() => setSidebarOpen(true)}
              >
                <Menu className="h-5 w-5" />
              </Button>
              <h2 className="ml-2 text-xl font-semibold text-gray-900 lg:ml-0">
                {navigation.find(item => item.id === currentPage)?.name || 'Dashboard'}
              </h2>
            </div>

            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <Button variant="ghost" size="sm" className="relative">
                <Bell className="h-5 w-5" />
                <Badge 
                  variant="destructive" 
                  className="absolute -top-1 -right-1 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
                >
                  3
                </Badge>
              </Button>

              {/* User menu */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                    <Avatar className="h-8 w-8">
                      <AvatarImage src={user?.profile_image_url} />
                      <AvatarFallback>{userInfo.initials}</AvatarFallback>
                    </Avatar>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent className="w-56" align="end" forceMount>
                  <DropdownMenuLabel className="font-normal">
                    <div className="flex flex-col space-y-1">
                      <p className="text-sm font-medium leading-none">{userInfo.name}</p>
                      <p className="text-xs leading-none text-muted-foreground">
                        {userInfo.email}
                      </p>
                    </div>
                  </DropdownMenuLabel>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    <User className="mr-2 h-4 w-4" />
                    <span>Profile</span>
                  </DropdownMenuItem>
                  <DropdownMenuItem>
                    <Settings className="mr-2 h-4 w-4" />
                    <span>Settings</span>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem onClick={handleLogout}>
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default Layout;

