/**
 * Dashboard Component for Mass Tracking System
 * Main dashboard with statistics, charts, and quick actions
 */

import { useState, useEffect } from 'react';
import { 
  Calendar, 
  TrendingUp, 
  Clock, 
  AlertTriangle, 
  CheckCircle, 
  Pause,
  Play,
  Plus,
  Eye
} from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';
import apiClient from '@/lib/api.js';
import { dateUtils, numberUtils, massUtils } from '@/lib/utils.js';
import '../App.css';

const Dashboard = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboardResponse, summaryResponse, alertsResponse] = await Promise.all([
        apiClient.getDashboard(),
        apiClient.getDashboardSummary(),
        apiClient.getDashboardAlerts()
      ]);

      setDashboardData({
        ...dashboardResponse.data,
        summary: summaryResponse.data,
        alerts: alertsResponse.data
      });
      setError(null);
    } catch (err) {
      console.error('Failed to load dashboard:', err);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <Card key={i} className="animate-pulse">
              <CardHeader className="pb-2">
                <div className="h-4 bg-gray-200 rounded w-3/4"></div>
              </CardHeader>
              <CardContent>
                <div className="h-8 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-full"></div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  const { summary, alerts, current_month_obligation, low_count_bulk_intentions, today_celebrations } = dashboardData;

  // Sample chart data (in a real app, this would come from the API)
  const monthlyData = [
    { month: 'Jan', masses: 25, personal: 3, bulk: 22 },
    { month: 'Feb', masses: 28, personal: 3, bulk: 25 },
    { month: 'Mar', masses: 30, personal: 3, bulk: 27 },
    { month: 'Apr', masses: 27, personal: 3, bulk: 24 },
    { month: 'May', masses: 32, personal: 3, bulk: 29 },
    { month: 'Jun', masses: 29, personal: 3, bulk: 26 },
  ];

  const intentionTypeData = [
    { name: 'Personal', value: summary?.monthly_progress?.completed || 0, color: '#8884d8' },
    { name: 'Bulk', value: summary?.month_masses - (summary?.monthly_progress?.completed || 0), color: '#82ca9d' },
    { name: 'Fixed Date', value: 5, color: '#ffc658' },
    { name: 'Special', value: 3, color: '#ff7300' },
  ];

  return (
    <div className="space-y-6">
      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Today's Masses</CardTitle>
            <Calendar className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.today_masses || 0}</div>
            <p className="text-xs text-muted-foreground">
              {today_celebrations?.length > 0 ? 'Completed today' : 'No masses today'}
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">This Month</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.month_masses || 0}</div>
            <p className="text-xs text-muted-foreground">
              +{summary?.month_masses - 20 || 0} from last month
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Active Bulk Intentions</CardTitle>
            <Pause className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.active_bulk_intentions || 0}</div>
            <p className="text-xs text-muted-foreground">
              {low_count_bulk_intentions?.length || 0} running low
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Notifications</CardTitle>
            <AlertTriangle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.unread_notifications || 0}</div>
            <p className="text-xs text-muted-foreground">
              {alerts?.urgent_count || 0} urgent alerts
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Alerts Section */}
      {alerts?.alerts?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              Alerts & Reminders
            </CardTitle>
            <CardDescription>
              Important notifications requiring your attention
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {alerts.alerts.slice(0, 3).map((alert, index) => (
                <Alert key={index} variant={alert.priority === 'urgent' ? 'destructive' : 'default'}>
                  <AlertTriangle className="h-4 w-4" />
                  <AlertTitle className="flex items-center justify-between">
                    {alert.title}
                    <Badge variant={alert.priority === 'urgent' ? 'destructive' : 'secondary'}>
                      {alert.priority}
                    </Badge>
                  </AlertTitle>
                  <AlertDescription>{alert.message}</AlertDescription>
                </Alert>
              ))}
              {alerts.alerts.length > 3 && (
                <Button variant="outline" size="sm" className="w-full">
                  View All {alerts.alerts.length} Alerts
                </Button>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Monthly Progress */}
      {current_month_obligation && (
        <Card>
          <CardHeader>
            <CardTitle>Monthly Personal Masses</CardTitle>
            <CardDescription>
              Progress towards your 3 required personal masses this month
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {current_month_obligation.completed_count} of {current_month_obligation.target_count} completed
                </span>
                <span className="text-sm text-muted-foreground">
                  {numberUtils.formatPercentage(
                    current_month_obligation.completed_count, 
                    current_month_obligation.target_count
                  )}
                </span>
              </div>
              <Progress 
                value={numberUtils.calculatePercentage(
                  current_month_obligation.completed_count, 
                  current_month_obligation.target_count
                )} 
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>
                  {current_month_obligation.target_count - current_month_obligation.completed_count} remaining
                </span>
                <span>
                  Due: {dateUtils.formatDate(new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0))}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly Masses Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Monthly Mass Celebrations</CardTitle>
            <CardDescription>
              Your mass celebration trends over the past 6 months
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="month" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="personal" stackId="a" fill="#8884d8" name="Personal" />
                <Bar dataKey="bulk" stackId="a" fill="#82ca9d" name="Bulk" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Intention Types Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Mass Types Distribution</CardTitle>
            <CardDescription>
              Breakdown of mass types celebrated this month
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={intentionTypeData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {intentionTypeData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Bulk Intentions Status */}
      {summary?.bulk_intentions_summary?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Active Bulk Intentions</CardTitle>
            <CardDescription>
              Current status of your bulk mass intentions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {summary.bulk_intentions_summary.map((intention) => (
                <div key={intention.id} className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-medium">{intention.title}</h4>
                      <Badge variant={intention.is_paused ? 'secondary' : 'default'}>
                        {intention.is_paused ? 'Paused' : 'Active'}
                      </Badge>
                      <Badge variant={massUtils.getBulkStatusLevel(intention.current_count, intention.total_count) === 'urgent' ? 'destructive' : 'outline'}>
                        {intention.status_level}
                      </Badge>
                    </div>
                    <div className="mt-2">
                      <div className="flex items-center justify-between text-sm text-muted-foreground mb-1">
                        <span>{intention.current_count} remaining</span>
                        <span>
                          {numberUtils.formatPercentage(
                            intention.total_count - intention.current_count, 
                            intention.total_count
                          )} complete
                        </span>
                      </div>
                      <Progress 
                        value={numberUtils.calculatePercentage(
                          intention.total_count - intention.current_count, 
                          intention.total_count
                        )} 
                        className="w-full"
                      />
                    </div>
                  </div>
                  <div className="flex items-center space-x-2 ml-4">
                    {intention.is_paused ? (
                      <Button size="sm" variant="outline">
                        <Play className="h-4 w-4 mr-1" />
                        Resume
                      </Button>
                    ) : (
                      <Button size="sm" variant="outline">
                        <Pause className="h-4 w-4 mr-1" />
                        Pause
                      </Button>
                    )}
                    <Button size="sm" variant="outline">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Today's Celebrations */}
      {today_celebrations?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Today's Mass Celebrations</CardTitle>
            <CardDescription>
              Masses you've celebrated today
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {today_celebrations.map((celebration) => (
                <div key={celebration.id} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center space-x-3">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <div>
                      <p className="font-medium">
                        {celebration.mass_time ? dateUtils.formatTime(celebration.mass_time) : 'Time not specified'}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {celebration.location || 'Location not specified'}
                      </p>
                    </div>
                  </div>
                  <Badge variant="outline">
                    {massUtils.getCelebrationTypeDisplay(celebration.celebration_type)}
                  </Badge>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>
            Common tasks and shortcuts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Button className="h-20 flex flex-col items-center justify-center space-y-2">
              <Plus className="h-6 w-6" />
              <span>Record Mass</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <Calendar className="h-6 w-6" />
              <span>View Calendar</span>
            </Button>
            <Button variant="outline" className="h-20 flex flex-col items-center justify-center space-y-2">
              <TrendingUp className="h-6 w-6" />
              <span>View Statistics</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Dashboard;

