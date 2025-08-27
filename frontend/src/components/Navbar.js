import React, { useState } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Avatar,
} from '@mui/material';
import {
  AccountCircle,
  Dashboard,
  Chat,
  History,
  ExitToApp,
  SmartToy,
} from '@mui/icons-material';
import { useAuth } from '../contexts/AuthContext';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorEl, setAnchorEl] = useState(null);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleNavigation = (path) => {
    navigate(path);
  };

  const handleLogout = () => {
    handleMenuClose();
    logout();
  };

  const isActive = (path) => {
    return location.pathname === path;
  };

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar>
        <Typography
          variant="h6"
          component="div"
          sx={{ flexGrow: 1, cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          Virtual Expert AI
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Button
            color="inherit"
            startIcon={<Dashboard />}
            onClick={() => handleNavigation('/')}
            sx={{
              backgroundColor: isActive('/') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
            }}
          >
            Dashboard
          </Button>
          <Button
            color="inherit"
            startIcon={<Chat />}
            onClick={() => handleNavigation('/chat')}
            sx={{
              backgroundColor: isActive('/chat') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
            }}
          >
            Chat
          </Button>
          <Button
            color="inherit"
            startIcon={<History />}
            onClick={() => handleNavigation('/history')}
            sx={{
              backgroundColor: isActive('/history') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
            }}
          >
            History
          </Button>
          <Button
            color="inherit"
            startIcon={<SmartToy />}
            onClick={() => handleNavigation('/models')}
            sx={{
              backgroundColor: isActive('/models') ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
            }}
          >
            Models
          </Button>

          <IconButton
            size="large"
            edge="end"
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleMenuOpen}
            color="inherit"
          >
            <Avatar sx={{ width: 32, height: 32 }}>
              {user?.username ? user.username.charAt(0).toUpperCase() : <AccountCircle />}
            </Avatar>
          </IconButton>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => { handleMenuClose(); handleNavigation('/profile'); }}>
              <AccountCircle sx={{ mr: 1 }} />
              Profile
            </MenuItem>
            <MenuItem onClick={handleLogout}>
              <ExitToApp sx={{ mr: 1 }} />
              Logout
            </MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;